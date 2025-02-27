# Textable AI
## replies to google voice text messages with ai generated replies, allowing sms converstations with ai models. 

* responds to sms messages in 15-30 seconds
* scrapes inbox for text notifs from gvoice
* uses the free huggingface inference api for the default model(llama 3.2 3b instruct)
* creates context windows for each user

Issues:
* unfinished sections for generating images
* mail.noop() socket errors

Things to add:
* a proper cl interface
* have message 'keywords' to allow message passthrough or select other models or clear memory
  -'NOREPLY', 'UNCENSORED', 'CLEAR'
