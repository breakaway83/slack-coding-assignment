import imaplib
import logging
import email
from mailbox import mbox
import re
import os
from helmut.util.Constants import Constants as const

LOGGER = logging.getLogger('email alert helper log')
class EmailHelpers(object):


    def __init__(self):
        global email_attachments
        global detach_dir
        email_attachments = []

    def connecttoInbox(self,username,password,
                       imapserver=const.TestConstants['SMTP_GMAIL_SERVER'],
                       folder="Inbox"):
        """
        Connects to the inbox identified by the imap server, username 
        and password
        """
        
        self.mail = imaplib.IMAP4_SSL(imapserver)
        self.mail.login(username, password)
        self.mail.select(folder)       
        

    def searchEmail(self,searchkey, searchvalue ):
        """
        searches the Inbox for messages using the search phrase
        returns the message Ids of the retrieved messages
        """
        LOGGER.info('search key and value is {0} and {1}'.format(searchkey,searchvalue))
        typ, msgnums = self.mail.search(None,searchkey,searchvalue)
        for msg in msgnums[0].split():
            type, data = self.mail.fetch(msg,'(RFC822)')

        return msgnums
    

    def deleteEmail(self,msgslist):
        """
        delete the message corresponding to the msg Id from the Inbox
        """        
        LOGGER.info("deletes that particular email")
        print msgslist
        if msgslist:
            for msgId in msgslist[0].split():
                self.mail.store(msgId, '+FLAGS', '\\Deleted')
                
        self.mail.expunge()
        

    def deleteAllEmails(self):
        """
        deletes all the emails in the Inbox
        """
        msgnums = searchEmail(' ')
        for msg in msgnums[0].split():
            self.mail.store(msg, '+FLAGS', '\\Deleted')

        self.mail.expunge()


    def logoutEmail(self):
        """
        Logs out of the email
        """
        self.mail.logout()


    def getEmailAttachments(self,msgs):
        """
        Downloads the attachments of all the emails in the msgs (list of msg Id)
        returns a list containing names of all attachments in the emails
        """
        LOGGER.info( "Method to get email attachments")
        for emailid in msgs:
            resp, data = self.mail.fetch(emailid, "(RFC822)")
            email_body = data[0][1]
            m = email.message_from_string(email_body)

            if m.get_content_maintype() != 'multipart':
                continue

            for part in m.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

            filename = part.get_filename()
            email_attachments.append(filename)

        return email_attachments


    def downloadEmailAttachments(self,detach_dir):
        """
        downloads and saves the attachments in the email_attachments list        
        """
        LOGGER.info( "Method to read contents of an email attachment")

        detach_dir = os.path.curdir 

        for attachment in email_attachments:
            att_path = os.path.join(detach_dir, attachment)
            if not os.path.isfile(att_path) :
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()



    def searchEmailAttachments(self,searchTerm):
        """
        Searches the downloaded attachments for the search term
        returns True if the search term was found
        """
        LOGGER.info( "Searches email attachments")
        for attachment in email_attachments:
            mailfile = open(attachment, 'r')
            
            filetext = mailfile.read()
            mailfile.close()
            matches = re.findall(searchTerm,mailfile)


        return matches

    def msgBodyContains(self,msgs,content):
        for emailid in msgs[0].split():
            resp, data = self.mail.fetch(emailid, "(RFC822)")
            email_body = data[0][1]
            
            if(content in email_body):
                return True
    
        return False
        

    def getContentType(self,msgs):
        """
        returns the list of content type, main content type and sub-content type
        for inline and attached email contents
        """
        content_type = []
        main_content_type = []
        sub_content_type = []
        
        for emailid in msgs[0].split():
            resp, data = self.mail.fetch(emailid, '(RFC822)')
            email_body = data[0][1]
            m = email.message_from_string(email_body)

            for part in m.walk():
                content_type.append(part.get_content_type())
                main_content_type.append(part.get_content_maintype())
                sub_content_type.append(part.get_content_subtype())
                
        
        return content_type, main_content_type, sub_content_type
