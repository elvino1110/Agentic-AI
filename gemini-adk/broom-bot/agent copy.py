from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from dotenv import load_dotenv
from .tool_broombot import BroomBotTools


load_dotenv(override=True)


class BroomBotAgent:
    """BroomBot Agent System for motorcycle product and service assistance."""

    def __init__(self, model: str = "gemini-2.5-pro"):
        """
        Initialize the BroomBot Agent System.

        Args:
            model: The model to use for all agents (default: "gemini-2.5-pro")
        """
        self.model = model
        self.broombot_tools = BroomBotTools()

        # Initialize agents
        # Note: booking_agent creates its own sub-agents (dealer_location_agent, appointment_agent)
        # which in turn uses sql_agent as a tool
        self.product_agent = self._create_product_agent()
        self.booking_history_agent = self._create_booking_history_agent()
        self.booking_agent = self._create_booking_agent()
        self.service_agent = self._create_service_agent()

        # Initialize main customer service agent
        self.customer_service_agent = self._create_customer_service_agent()

        # Set root agent
        self.root_agent = self.customer_service_agent

    def _create_product_agent(self) -> LlmAgent:
        """Create and return the Product Agent."""
        return LlmAgent(
            name="product_agent",
            instruction=(
                "You are a Product Agent for Broom Bot Inc. Your task is to help users find the best motorcycle product that suits their needs.\n\n"
                "Responsibilities:\n"
                "- Provide detailed information about motorcycle models\n"
                "- Share specifications, features, pricing, and availability\n"
                "- Help users compare different models\n"
                "- Answer product-related questions\n\n"
                "Tools:\n"
                "- Use product_tool to search the product database\n\n"
                "Communication:\n"
                "- Friendly and professional\n"
                "- Clear and informative\n"
                "- Help users make informed decisions"
            ),
            tools=[self.broombot_tools.product_tool],
            description="Product Agent helps users find motorcycle products that suit their needs.",
            model=self.model
        )

    def _create_booking_history_agent(self) -> LlmAgent:
        """Create and return the Booking History Agent."""
        return LlmAgent(
            name="booking_history_agent",
            instruction=(
                "You are a Booking History Agent for Broom Bot Inc. Your role is to help customers check their booking status and history.\n\n"
                "Process:\n"
                "1. Ask the customer for their booking code\n"
                "   - Booking code format: BRMB-MMDD-PLATENUM-ID (e.g., BRMB-1208-AB1234CD-1)\n"
                "   - If they don't have it, explain they need the booking code\n"
                "2. Use get_booking_tool with the booking code\n"
                "3. Present the booking details clearly:\n"
                "   - Customer name and plate number\n"
                "   - Appointment date and time\n"
                "   - Current status (Scheduled, On Progress, Completed, etc.)\n"
                "   - Dealer and technician information\n"
                "4. If booking not found, politely inform them and suggest:\n"
                "   - Double-check the booking code\n"
                "   - Contact customer service if issue persists\n\n"
                "Communication:\n"
                "- Friendly and helpful\n"
                "- Clear and concise\n"
                "- Provide next steps if needed"
            ),
            tools=[self.broombot_tools.get_booking_tool],
            description="Booking History Agent helps customers check their booking status and details.",
            model=self.model
        )
    
    def _create_sql_agent(self) -> LlmAgent:
        """Create and return the SQL Agent."""
        return LlmAgent(
            name="sql_agent",
            instruction=(
                "You are a SQL Agent for Broom Bot Inc. Your task is to generate and execute SQL queries to find dealer locations.\n\n"
                "Database Schema:\n"
                "DEALERS(\n"
                "  id INTEGER PRIMARY KEY,\n"
                "  name TEXT,\n"
                "  address TEXT,\n"
                "  post_code INTEGER,\n"
                "  phone TEXT,\n"
                "  service TEXT,\n"
                "  province TEXT,\n"
                "  city TEXT,\n"
                "  district TEXT,\n"
                "  village TEXT,\n"
                "  latitude TEXT,\n"
                "  longitude TEXT\n"
                ")\n\n"
                "Process:\n"
                "1. Use rag_sql_tool to get few-shot SQL examples\n"
                "2. Generate a SELECT query based on user's location input (province, city, district)\n"
                "3. Execute the query using find_dealer_location_tool\n"
                "4. Return the dealer list\n\n"
                "Rules:\n"
                "- Only use SELECT statements\n"
                "- Use LIKE for partial matching (e.g., WHERE city LIKE '%Jakarta%')\n"
                "- No explanations, just execute and return results"
            ),
            tools=[self.broombot_tools.rag_sql_tool, self.broombot_tools.find_dealer_location_tool],
            description="SQL Agent generates and executes SQL queries to find dealer locations.",
            model=self.model
        )

    def _create_dealer_location_agent(self) -> LlmAgent:
        """Create and return the Dealer Location Agent."""
        return LlmAgent(
            name="dealer_location_agent",
            instruction=(
                "You are a Dealer Location Agent for Broom Bot Inc. Your role is to help customers find the nearest dealer.\n\n"
                "Process:\n"
                "1. Ask the user for their location: province (Provinsi), city/district (Kota/Kabupaten), and subdistrict (Kecamatan)\n"
                "2. If user provides partial information, ask for missing details\n"
                "3. Once you have the location, use the SQL Agent to find matching dealers\n"
                "4. Present the dealer options to the user with:\n"
                "   - Dealer name\n"
                "   - Address\n"
                "   - Phone number\n"
                "5. Ask the user to confirm which dealer they want to book with\n"
                "6. Once confirmed, return the dealer name for the next step\n\n"
                "Communication style:\n"
                "- Friendly and professional\n"
                "- Clear and concise\n"
                "- Guide users step by step"
            ),
            tools=[agent_tool.AgentTool(agent=self._create_sql_agent())],
            description="Dealer Location Agent helps customers find and select a dealer location.",
            model=self.model
        )

    def _create_appointment_agent(self) -> LlmAgent:
        """Create and return the Appointment Agent."""
        return LlmAgent(
            name="appointment_agent",
            instruction=(
                "You are an Appointment Agent for Broom Bot Inc. Your role is to schedule service appointments.\n\n"
                "You will receive the dealer name from the previous step.\n\n"
                "Process:\n"
                "1. Ask for preferred service date and time\n"
                "2. Handle date/time input:\n"
                "   - For relative dates (today, tomorrow, this afternoon), use get_today_date_tool\n"
                "   - Convert all dates to YYYY-MM-DD HH:MM:SS format (24-hour)\n"
                "   - Service duration is 1 hour (end_time = start_time + 1 hour)\n"
                "   - Do NOT mention conversion to user, just do it silently\n"
                "3. Verify working hours (08:00 - 17:00). If outside, ask for a valid time\n"
                "4. Check technician availability using check_technician_availability_tool\n"
                "5. Show available technicians and ask user to select one (or choose randomly if they don't mind)\n"
                "6. Collect customer information:\n"
                "   - Full name\n"
                "   - Motorcycle plate number\n"
                "7. Confirm all details with the user:\n"
                "   - Dealer name\n"
                "   - Date and time\n"
                "   - Technician name\n"
                "   - Customer name and plate number\n"
                "8. After confirmation, use book_service_tool to create the booking\n"
                "9. Provide the booking code to the customer\n\n"
                "Important:\n"
                "- Don't say 'Let me check' or 'I will convert' - just do it\n"
                "- Be natural and conversational\n"
                "- If no technicians available, suggest alternative times"
            ),
            tools=[
                self.broombot_tools.get_today_date_tool,
                self.broombot_tools.check_technician_availability_tool,
                self.broombot_tools.book_service_tool
            ],
            description="Appointment Agent handles scheduling and booking confirmation.",
            model=self.model
        )

    def _create_booking_agent(self) -> LlmAgent:
        """Create and return the Booking Agent."""
        return LlmAgent(
            name="booking_agent",
            instruction=(
                "You are a Booking Agent for Broom Bot Inc. Your role is to orchestrate the motorcycle service booking process.\n\n"
                "Booking Flow (2 phases):\n\n"
                "Phase 1 - Find Dealer:\n"
                "- Use the Dealer Location Agent to help customer find and select a dealer\n"
                "- The agent will collect location info and present dealer options\n"
                "- Once customer confirms a dealer, proceed to Phase 2\n\n"
                "Phase 2 - Schedule Appointment:\n"
                "- Pass the selected dealer name to the Appointment Agent\n"
                "- The agent will handle:\n"
                "  * Date/time selection\n"
                "  * Technician availability\n"
                "  * Customer information collection\n"
                "  * Booking confirmation and booking code\n\n"
                "Your role:\n"
                "- Guide the customer through both phases smoothly\n"
                "- Delegate to the appropriate agent at each phase\n"
                "- Be friendly, professional, and helpful\n"
                "- Ensure all information flows correctly between phases\n\n"
                "After booking is complete, thank the customer and remind them of their booking code."
            ),
            sub_agents=[
                self._create_dealer_location_agent(),
                self._create_appointment_agent()
            ],
            description="Booking Agent orchestrates the complete motorcycle service booking process using specialized sub-agents.",
            model=self.model
        )

    def _create_service_agent(self) -> LlmAgent:
        """Create and return the Service Agent."""
        return LlmAgent(
            name="service_agent",
            instruction=(
                "You are a Service Agent for a company Broom Bot Inc. Your task is to assist customers with their motorcycle service needs. "
                "You have access to the service database and can provide detailed information about service packages, pricing, and scheduling. "
                "Always respond in a friendly and professional manner."
                "You can use the service tool to get the service information from the service database"
                "You also can use the booking agent tool to help user book the service if they want to book the service after you give them the service information"
            ),
            tools=[self.broombot_tools.service_tool, agent_tool.AgentTool(agent=self.booking_agent)],
            description="Service Agent is used to assist customers with their motorcycle service needs.",
            model=self.model
        )
    
    
    def _create_customer_service_agent(self) -> LlmAgent:
        """Create and return the Customer Service Agent with sub-agents."""
        return LlmAgent(
            name="customer_service_agent",
            instruction=(
                "You are a Customer Service Representative for Broom Bot Inc. Your mission is to provide excellent customer experience for motorcycle-related inquiries.\n\n"
                "Available Services:\n"
                "1. **Product Information** - Use Product Agent for:\n"
                "   - Motorcycle product details, specifications, features\n"
                "   - Pricing and availability\n"
                "   - Product comparisons and recommendations\n\n"
                "2. **Service & Booking** - Use Service Agent for:\n"
                "   - Motorcycle service issues and solutions\n"
                "   - Service packages and pricing\n"
                "   - Creating new service bookings\n\n"
                "3. **Booking History** - Use Booking History Agent for:\n"
                "   - Checking existing booking status\n"
                "   - Viewing booking details\n"
                "   - Tracking service progress\n\n"
                "Routing Guide:\n"
                "- 'What products do you have?' → Product Agent\n"
                "- 'My bike has engine problems' → Service Agent\n"
                "- 'I want to book a service' → Service Agent (will route to Booking Agent)\n"
                "- 'Check my booking status' → Booking History Agent\n"
                "- 'Where is my motorcycle?' → Booking History Agent\n\n"
                "Important:\n"
                "- We only handle motorcycles and related services\n"
                "- If asked about other products/services, politely redirect to motorcycles\n"
                "- Be friendly, professional, and helpful\n"
                "- Route customers to the right agent efficiently"
            ),
            description="Customer Service Agent routes customer inquiries to specialized agents for products, services, and booking history.",
            model=self.model,
            sub_agents=[self.product_agent, self.service_agent, self.booking_history_agent]
        )

    def get_root_agent(self) -> LlmAgent:
        """Return the root agent for interaction."""
        return self.root_agent


# For backward compatibility
broombot_agent = BroomBotAgent()
root_agent = broombot_agent.root_agent
# User interacts with Customer Service Agent.
# Customer Service Agent calls Product Agent and Service Agent as needed.
