import os
from typing import Dict
from agents import Agent, function_tool
import AIRPALibrary

ailabs = AIRPALibrary.AIRPALibrary()

@function_tool
def send_email(subject: str, body: str) -> Dict[str, str]:
    """ Send out an email with the given subject and HTML body """
    
    email_to = 'muhammad.fakhrurrozi@ai.astra.co.id'
    email_from = 'elvino.dwisaputra@ai.astra.co.id'
    ailabs.send_email(subject=subject, content=f"""{body}""", to=email_to, sender=email_from)
    return {"status": "success"}

INSTRCTIONS = """You are able to send a nicely formatted HTML email based on the detailed report.
You will be provided with a detail report, you should use your tool to send one email, providing the
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="EmailAgent",
    instructions=INSTRCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
  