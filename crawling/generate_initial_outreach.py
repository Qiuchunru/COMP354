# Hardcoded values
YOUR_NAME = ""
YOUR_TITLE = "Vice-President"

email_template = """
Subject:

Sponsorship opportunity for {company_name} with HackCanada student association annual ConUHacks event

Body:

Hello {recipient_name},

My name is {your_name} and I am reaching out to you at {company_name} as {your_title} of Sponsorship for the HackCanada student association. We are a student group focused on bringing together a community of developers and programmers through experiential learning opportunities. This January, we are hosting the 10th edition of our annual Hackathon event, ConUHacks X, where over 1000 students from across Canada (and beyond) will compete in teams for 24 hours straight to produce innovative and creative projects. We would like to invite {company_name} to be a key sponsor for ConUHacks X, taking place on January 24-25, 2026 at Concordia University's John Molson Building{location}.

Either through a booth at our career fair, access to participants' CVs, or even a post-event recruitment email, we believe that this partnership would provide {company_name} with the unique opportunity to meet with (and recruit from) over 1000 top-tier engineering and computer science students from Montreal and beyond, who will one day be key stakeholders in their fields. As well, sponsoring ConUHacks opens up an exceptional avenue to promote your company to a vibrant student community, both through our event's branding or by sending company representatives as mentors or judges for our competition.

We would be happy to go over our sponsorship package and answer any questions you might have in a short 30 minute meeting, or by email if you prefer.

Thank you for your time and consideration, I look forward to hearing from you and to potentially working together on our event!

Thank you,

{your_name}
"""

def generate_email(company_name, recipient_name, location):
    if not recipient_name.strip():
        recipient_name = company_name  # Default to company name if no recipient name is provided
    
    return email_template.format(
        recipient_name=recipient_name,
        your_name=YOUR_NAME,
        company_name=company_name,
        your_title=YOUR_TITLE,
        location=location
    )

# Input prompts
def main():
    while True:
        while True:
            company_name = input("Enter the company name: ").strip()
            if company_name:
                break
            else:
                print("Company name cannot be blank. Please enter a valid company name.")
        recipient_name = input("Enter the recipient's name (leave blank to use company name): ").strip()

        # Ask if the recipient is local; default to Montreal, Quebec if blank
        local_input = input("Is the recipient local? (y for yes, blank for no): ").strip().lower()
        if local_input == 'y':
            location = ""
        else:
            location = " in Montreal, Quebec"

        email = generate_email(company_name, recipient_name, location)
        print("\n" + "="*80)
        print(email)
        print("="*80)
        print("\n")
        input("Press enter to generate another email: ")

if __name__ == "__main__":
    main()
