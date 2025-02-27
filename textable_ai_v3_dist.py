import imaplib
import email
from email.header import decode_header
import time
import smtplib
import re 
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from huggingface_hub import InferenceClient

# email account credentials
username = "email here"
password = "password here (needs to be an app password from google)"
imap_server = "imap.gmail.com"
gvoice_address = "txt.voice.google.com"

users=[]
user_conversations = {}
imap_session_refresh_timer = 0
indicator = 0

#this is the free "demo" api for the llama model being used by defualt
client = InferenceClient(api_key="your_api_key")

# Connect to the email server
mail = imaplib.IMAP4_SSL(imap_server)
mail.login(username, password)
mail.select("Inbox")

# Track the latest email ID to detect new emails
status, messages = mail.search(None, "ALL")
email_ids = messages[0].split()
latest_email_id = email_ids[-1]

def extract_email_content(msg):
    # Check if the email message is multipart
    if msg.is_multipart():
        for part in msg.walk():
            # Get the content type of the email part
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Skip attachments and non-text parts
            if content_type == "text/plain" and "attachment" not in content_disposition:
                # Decode the email body
                body = part.get_payload(decode=True).decode()
                #return isolate_latest_reply(body)
                return body
            elif content_type == "text/html" and "attachment" not in content_disposition:
                # Handle HTML content if needed
                body = part.get_payload(decode=True).decode()
                #return isolate_latest_reply(body)
                return body
    else:
        # For non-multipart emails
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            body = msg.get_payload(decode=True).decode()
            return isolate_latest_reply(body)
        elif content_type == "text/html":
            body = msg.get_payload(decode=True).decode()
            #return isolate_latest_reply(body)
            return body
        
def get_sender_email(msg):
    # Get the "From" header
    from_header = msg.get("From")
    
    # Decode the "From" header if it contains encoded words
    if from_header:
        decoded_from = decode_header(from_header)[0]
        if isinstance(decoded_from[0], bytes):
            sender = decoded_from[0].decode(decoded_from[1] if decoded_from[1] else 'utf-8')
        else:
            sender = decoded_from[0]
    else:
        sender = "Unknown"
    
    return sender

def generate_response():
    #add the message to the users context window
    user_conversations[sender_email].append({"role": "user", "content": gvoice_message})
    #select the senders context window
    user_chat = user_conversations[sender_email]
    
    # the following is what generates shit (you can replace it with whatever)
    try:
        model_response = client.chat_completion(
            model="meta-llama/Llama-3.2-3B-Instruct",
            messages=user_chat,
            max_tokens=500,
            stream=False
        )
        content = model_response.choices[0].message.content

    except: #if its too many tokens
        del user_chat[0:len(user_chat) // 2]
        print("\nContext limit reached, older memory cleared.")
        model_response = client.chat_completion(
            model="meta-llama/Llama-3.2-3B-Instruct",
            messages=user_chat,
            max_tokens=500,
            stream=False
        )
        content = "Context limit reached, older memory cleared. Response: " + model_response.choices[0].message.content

    # send the generated reply
    cleaned_content = " ".join(re.split("\s+", content, flags=re.UNICODE))
    msg = MIMEText(cleaned_content)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(username, password)
    server.sendmail(username, sender_email, msg.as_string())
    server.quit()   
    print(f"\nReply generated: {content}")    

    #append the response to the context window  
    user_conversations[sender_email].append({"role": "assistant", "content": content})

def isolate_latest_reply(body):
    # Define common patterns that indicate the start of quoted content
    patterns = [
        r"On\s.+\swrote:",      # Matches "On [date], [name] wrote:"
        r"From:.+",             # Matches "From: [name]"
        r"Sent:.+",             # Matches "Sent: [date]"
        r">",                   # Matches lines starting with ">"
    ]
    
    # Compile the patterns into a single regex
    quote_pattern = re.compile("|".join(patterns), re.MULTILINE)
    
    # Split the body at the first occurrence of a quotation pattern
    split_body = re.split(quote_pattern, body, maxsplit=1)
    
    # Return the part before the quoted content
    return split_body[0].strip()

def extract_text_between_markers(data: str) -> str:
    start_marker = "<https://voice.google.com>"
    end_marker = "YOUR ACCOUNT"

    # Find the start and end positions of the text you want to extract
    start_pos = data.find(start_marker) + len(start_marker)
    end_pos = data.find(end_marker, start_pos)

    # Extract the text between the markers
    if start_pos != -1 and end_pos != -1:
        return data[start_pos:end_pos].strip()
    else:
        return ""  # Return an empty string if markers are not found
    
def ai_mode():     
    global latest_email_id
    global imap_session_refresh_timer
    global mail
    global indicator
    while True:
        if indicator == 1:
            print("                        ", end='\r')
            print("listening for emails", end = "\r")
        elif indicator == 2:
            print("listening for emails.", end='\r' )
        elif indicator == 3:
            print("listening for emails..", end='\r' )
        elif indicator == 4:
            indicator = 0
            print("listening for emails...", end='\r' )

        if imap_session_refresh_timer == 60:
            imap_session_refresh_timer = 0
            mail.logout()
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(username, password)
            mail.select("Inbox")
            print("imap session renewed.")
        try:
            mail.noop() # FINALLLYY FUICKING WOEKRRKASODIUJ PEISFHIUOPAHFIOHAEDP YESSSSSS IT WORKS it just needed this bruh wtf
        except:
            mail.noop()
        finally:
            # Check for new emails
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            new_latest_email_id = email_ids[-1]
        
            # If there's a new email
            if new_latest_email_id != latest_email_id:
                latest_email_id = new_latest_email_id
                # Fetch the new email
                status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
            
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        raw_email = response_part[1]
                        msg = email.message_from_bytes(raw_email)
                        #print(msg)
                        # Extract and print the email content
                        email_body = extract_email_content(msg)
                        global sender_email
                        sender_email = get_sender_email(msg)
                        global gvoice_message
                        gvoice_message = extract_text_between_markers(email_body)
                        global full_prompt
                        #print(users)
                        print(sender_email)
                        print(gvoice_message)
                        #print(user_converstions)
                        #print(full_prompt)
                        if gvoice_address in sender_email: 
                            if sender_email in users:
                                generate_response()
                            else:
                                users.append(sender_email)
                                user_conversations[sender_email] = [{"role": "system", "content": "You are a helpful AI assistant."}]
                                generate_response()
                        
        imap_session_refresh_timer = imap_session_refresh_timer + 1
        indicator = indicator + 1
        time.sleep(1)   

ai_mode()
