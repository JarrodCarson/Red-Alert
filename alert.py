'''
Author: Jarrod Carson
'''

class Alert():
  '''
  An alert to be broadcast by the bot
  '''
  def __init__(self, author, subject, desc, date, time):
    self.subject = subject
    self.desc = desc
    self.date = date
    self.time = time
  
  async def get_attr(self):
    return {"author": self.author,
            "subject": self.subject,
            "desc": self.desc,
            "date": self.date,
            "time": self.time}