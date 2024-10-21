import ast
import base64
import logging
import re
import smtplib

import psycopg2

from odoo import Command, _, models, tools

from odoo.addons.base.models.ir_mail_server import MailDeliveryException

_logger = logging.getLogger(__name__)


class Mail(models.Model):
    _inherit = "mail.mail"

    def send_with_template(self, payslip, auto_commit=False, raise_exception=False):
        """Sends the selected emails immediately, ignoring their current
        state (mails that have already been sent should not be passed
        unless they should actually be re-sent).
        Emails successfully delivered are marked as 'sent', and those
        that fail to be deliver are marked as 'exception', and the
        corresponding error mail is output in the server logs.

        :param bool auto_commit: whether to force a commit of the mail status
            after sending each mail (meant only for scheduler processing);
            should never be True during normal transactions (default: False)
        :param bool raise_exception: whether to raise an exception if the
            email sending process has failed
        :return: True
        """
        for mail_server_id, smtp_from, batch_ids in self._split_by_mail_configuration():
            smtp_session = None
            try:
                smtp_session = self.env["ir.mail_server"].connect(
                    mail_server_id=mail_server_id, smtp_from=smtp_from
                )
            except Exception as exc:
                if raise_exception:
                    # To be consistent and backward compatible with mail_mail.send()
                    # raised exceptions, it is encapsulated into an Odoo
                    # MailDeliveryException
                    raise MailDeliveryException(  # noqa: B904
                        _("Unable to connect to SMTP Server"),
                        exc,
                    )
                else:
                    batch = self.browse(batch_ids)
                    batch.write({"state": "exception", "failure_reason": exc})
                    payslip.email_state = "exception"
                    batch._postprocess_sent_message(
                        success_pids=[], failure_type="mail_smtp"
                    )
            else:
                self.browse(batch_ids)._send_with_template(
                    #################################################
                    payslip,
                    #################################################
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    smtp_session=smtp_session,
                )
                _logger.info(
                    "Sent batch %s emails via mail server ID #%s",
                    len(batch_ids),
                    mail_server_id,
                )
            finally:
                if smtp_session:
                    smtp_session.quit()

    def _send_with_template(  # noqa: C901
        self, payslip, auto_commit=False, raise_exception=False, smtp_session=None
    ):
        IrMailServer = self.env["ir.mail_server"]
        IrAttachment = self.env["ir.attachment"]
        for mail_id in self.ids:
            success_pids = []
            failure_type = None
            processing_pid = None
            mail = None
            try:
                mail = self.browse(mail_id)
                if mail.state != "outgoing":
                    if mail.state != "exception" and mail.auto_delete:
                        mail.sudo().unlink()
                    continue

                # remove attachments if user send the link with the access_token
                body = mail.body_html or ""
                attachments = mail.attachment_ids
                for link in re.findall(r"/web/(?:content|image)/([0-9]+)", body):
                    attachments = attachments - IrAttachment.browse(int(link))

                # load attachment binary data with a separate read(), as prefetching all
                # `datas` (binary field) could bloat the browse cache, triggerring
                # soft/hard mem limits with temporary data.
                attachments = [
                    (a["name"], base64.b64decode(a["datas"]), a["mimetype"])
                    for a in attachments.sudo().read(["name", "datas", "mimetype"])
                    if a["datas"] is not False
                ]

                # specific behavior to customize the send email for notified partners
                email_list = []
                if mail.email_to:
                    email_list.append(mail._send_prepare_values())
                for partner in mail.recipient_ids:
                    values = mail._send_prepare_values(partner=partner)
                    values["partner_id"] = partner
                    email_list.append(values)

                # headers
                headers = {}
                ICP = self.env["ir.config_parameter"].sudo()
                bounce_alias = ICP.get_param("mail.bounce.alias")
                catchall_domain = ICP.get_param("mail.catchall.domain")
                if bounce_alias and catchall_domain:
                    headers["Return-Path"] = f"{bounce_alias}@{catchall_domain}"
                if mail.headers:
                    try:
                        headers.update(ast.literal_eval(mail.headers))
                    except Exception as e:
                        _logger.info(e)
                        pass

                # Writing on the mail object may fail (e.g. lock on user) which
                # would trigger a rollback *after* actually sending the email.
                # To avoid sending twice the same email, provoke the failure earlier
                mail.write(
                    {
                        "state": "exception",
                        "failure_reason": _(
                            "Error without exception. Probably due do "
                            "sending an email without computed recipients."
                        ),
                    }
                )
                #################################################
                payslip.email_state = "exception"
                #################################################
                # Update notification in a transient exception state to avoid concurrent
                # update in case an email bounces while sending all emails related to
                # current mail record.
                notifs = self.env["mail.notification"].search(
                    [
                        ("notification_type", "=", "email"),
                        ("mail_mail_id", "in", mail.ids),
                        ("notification_status", "not in", ("sent", "canceled")),
                    ]
                )
                if notifs:
                    notif_msg = _(
                        "Error without exception. Probably due do concurrent "
                        "access update of notification records. Please see with "
                        "an administrator."
                    )
                    notifs.sudo().write(
                        {
                            "notification_status": "exception",
                            "failure_type": "unknown",
                            "failure_reason": notif_msg,
                        }
                    )
                    # `test_mail_bounce_during_send`, force immediate
                    # update to obtain the lock. see
                    # rev. 56596e5240ef920df14d99087451ce6f06ac6d36
                    notifs.flush(
                        fnames=[
                            "notification_status",
                            "failure_type",
                            "failure_reason",
                        ],
                        records=notifs,
                    )

                # build an RFC2822 email.message.Message object and
                # send it without queuing
                res = None
                # TDE note: could be great to pre-detect missing to/cc
                # and skip sending it  to go directly to failed state update
                for email in email_list:
                    msg = IrMailServer.build_email(
                        email_from=mail.email_from,
                        email_to=email.get("email_to"),
                        subject=mail.subject,
                        body=email.get("body"),
                        body_alternative=email.get("body_alternative"),
                        email_cc=tools.email_split(mail.email_cc),
                        reply_to=mail.reply_to,
                        attachments=attachments,
                        message_id=mail.message_id,
                        references=mail.references,
                        object_id=mail.res_id and (f"{mail.res_id}-{mail.model}"),
                        subtype="html",
                        subtype_alternative="plain",
                        headers=headers,
                    )
                    processing_pid = email.pop("partner_id", None)
                    try:
                        res = IrMailServer.send_email(
                            msg,
                            mail_server_id=mail.mail_server_id.id,
                            smtp_session=smtp_session,
                        )
                        if processing_pid:
                            success_pids.append(processing_pid)
                        processing_pid = None
                    except AssertionError as error:
                        if str(error) == IrMailServer.NO_VALID_RECIPIENT:
                            # if we have a list of void emails for email_list ->
                            # email missing, otherwise generic email failure
                            if (
                                not email.get("email_to")
                                and failure_type != "mail_email_invalid"
                            ):
                                failure_type = "mail_email_missing"
                            else:
                                failure_type = "mail_email_invalid"
                            # No valid recipient found for this particular
                            # mail item -> ignore error to avoid blocking
                            # delivery to next recipients, if any. If this is
                            # the only recipient, the mail will show as failed.
                            _logger.info(
                                "Ignoring invalid recipients for mail.mail %s: %s",
                                mail.message_id,
                                email.get("email_to"),
                            )
                        else:
                            raise
                if res:  # mail has been sent at least once, no major exception occurred
                    mail.write(
                        {"state": "sent", "message_id": res, "failure_reason": False}
                    )
                    #################################################
                    payslip.email_state = "sent"
                    #################################################
                    _logger.info(
                        "Mail with ID %r and Message-Id %r successfully sent",
                        mail.id,
                        mail.message_id,
                    )
                    # /!\ can't use mail.state here, as mail.refresh() will
                    # cause an error see
                    # revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
                mail._postprocess_sent_message(
                    success_pids=success_pids, failure_type=failure_type
                )
            except MemoryError:
                # prevent catching transient MemoryErrors, bubble up to notify
                # user or abort cron job instead of marking the mail as failed
                _logger.exception(
                    "MemoryError while processing mail with ID %r and Msg-Id %r. "
                    "Consider raising the --limit-memory-hard startup option",
                    mail.id,
                    mail.message_id,
                )
                # mail status will stay on ongoing since transaction will be rollback
                raise
            except (psycopg2.Error, smtplib.SMTPServerDisconnected):
                # If an error with the database or SMTP session occurs,
                # chances are that the cursor or SMTP session are unusable,
                # causing further errors when trying to save the state.
                _logger.exception(
                    "Exception while processing mail with ID %r and Msg-Id %r.",
                    mail.id,
                    mail.message_id,
                )
                raise
            except Exception as e:
                failure_reason = tools.ustr(e)
                _logger.exception(
                    "failed sending mail (id: %s) due to %s", mail.id, failure_reason
                )
                mail.write({"state": "exception", "failure_reason": failure_reason})
                #################################################
                payslip.email_state = "exception"
                #################################################
                mail._postprocess_sent_message(
                    success_pids=success_pids,
                    failure_reason=failure_reason,
                    failure_type="unknown",
                )
                if raise_exception:
                    if isinstance(e, (AssertionError, UnicodeEncodeError)):
                        if isinstance(e, UnicodeEncodeError):
                            value = "Invalid text: %s" % e.object
                        else:
                            value = ". ".join(e.args)
                        raise MailDeliveryException(value)  # noqa: B904
                    raise

            if auto_commit is True:
                self._cr.commit()
        return True


class Mail(models.Model):
    _inherit = "mail.template"

    def send_mail_template(
        self,
        res_id,
        payslip,
        force_send=False,
        raise_exception=False,
        email_values=None,
        notif_layout=False,
    ):
        """Generates a new mail.mail. Template is rendered on record given by
        res_id and model coming from template.

        :param int res_id: id of the record to render the template
        :param bool force_send: send email immediately; otherwise use the mail
            queue (recommended);
        :param dict email_values: update generated mail with those values to further
            customize the mail;
        :param str notif_layout: optional notification layout to encapsulate the
            generated email;
        :returns: id of the mail.mail that was created"""

        # Grant access to send_mail only if access to related document
        self.ensure_one()
        self._send_check_access([res_id])

        Attachment = self.env[
            "ir.attachment"
        ]  # TDE FIXME: should remove default_type from context

        # create a mail_mail based on values, without attachments
        values = self.generate_email(
            res_id,
            [
                "subject",
                "body_html",
                "email_from",
                "email_to",
                "partner_to",
                "email_cc",
                "reply_to",
                "scheduled_date",
            ],
        )
        values["recipient_ids"] = [
            Command.link(pid) for pid in values.get("partner_ids", list())
        ]
        values["attachment_ids"] = [
            Command.link(aid) for aid in values.get("attachment_ids", list())
        ]
        values.update(email_values or {})
        attachment_ids = values.pop("attachment_ids", [])
        attachments = values.pop("attachments", [])
        # add a protection against void email_from
        if "email_from" in values and not values.get("email_from"):
            values.pop("email_from")
        # encapsulate body
        if notif_layout and values["body_html"]:
            try:
                template = self.env.ref(notif_layout, raise_if_not_found=True)
            except ValueError:
                _logger.warning(
                    "QWeb template {} not found when sending template {}. "
                    "Sending without layouting.".format(notif_layout, self.name)
                )
            else:
                record = self.env[self.model].browse(res_id)
                model = self.env["ir.model"]._get(record._name)

                if self.lang:
                    lang = self._render_lang([res_id])[res_id]
                    template = template.with_context(lang=lang)
                    model = model.with_context(lang=lang)

                template_ctx = {
                    "message": self.env["mail.message"]
                    .sudo()
                    .new(
                        dict(body=values["body_html"], record_name=record.display_name)
                    ),
                    "model_description": model.display_name,
                    "company": "company_id" in record
                    and record["company_id"]
                    or self.env.company,
                    "record": record,
                }
                body = template._render(
                    template_ctx, engine="ir.qweb", minimal_qcontext=True
                )
                values["body_html"] = self.env[
                    "mail.render.mixin"
                ]._replace_local_links(body)
        mail = self.env["mail.mail"].sudo().create(values)

        # manage attachments
        for attachment in attachments:
            attachment_data = {
                "name": attachment[0],
                "datas": attachment[1],
                "type": "binary",
                "res_model": "mail.message",
                "res_id": mail.mail_message_id.id,
            }
            attachment_ids.append((4, Attachment.create(attachment_data).id))
        if attachment_ids:
            mail.write({"attachment_ids": attachment_ids})

        if force_send:
            #################################################
            mail.send_with_template(payslip, raise_exception=raise_exception)
            #################################################
        return mail.id  # TDE CLEANME: return mail + api.returns ?
