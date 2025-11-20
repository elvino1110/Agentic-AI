from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import agent_tool
from google.adk.tools.function_tool import FunctionTool
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

        # Initialize the 4 main agents
        # Note: booking_agent creates its own sub-agents:
        #   - dealer_location_agent (with sql_agent)
        #   - appointment_agent
        #   - check_booking_agent
        # Note: lead_analysis_agent is a SequentialAgent workflow with 4 phases:
        #   - planning_agent → analyst_agent → engineer_agent → result_analyst_agent
        self.product_agent = self._create_product_agent()
        self.service_agent = self._create_service_agent()
        self.booking_agent = self._create_booking_agent()  # Handles create + check bookings
        self.lead_analysis_agent = self._create_lead_analysis_agent()  # Sequential workflow (4 phases)

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

    def _create_check_booking_agent(self) -> LlmAgent:
        """Create and return the Check Booking Agent (sub-agent for checking existing bookings)."""
        return LlmAgent(
            name="check_booking_agent",
            instruction=(
                "You are a Check Booking Agent for Broom Bot Inc. Your role is to retrieve and display existing booking information.\n\n"
                "Process:\n"
                "1. Ask the customer for their booking code\n"
                "   - Format: BRMB-MMDD-PLATENUM-ID (e.g., BRMB-1208-AB1234CD-1)\n"
                "2. Use get_booking_tool with the booking code\n"
                "3. Present booking details clearly\n"
                "4. If not found, suggest double-checking the code\n\n"
                "Communication: Friendly, clear, and helpful"
            ),
            tools=[self.broombot_tools.get_booking_tool],
            description="Check Booking Agent retrieves and displays existing booking information.",
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
                FunctionTool(self.broombot_tools.book_service_tool, require_confirmation=True)
            ],
            description="Appointment Agent handles scheduling and booking confirmation.",
            model=self.model
        )

    def _create_booking_agent(self) -> LlmAgent:
        """Create and return the unified Booking Management Agent."""
        return LlmAgent(
            name="booking_agent",
            instruction=(
                "You are a Booking Management Agent for Broom Bot Inc. You handle ALL booking-related tasks - both creating new bookings and checking existing ones.\n\n"
                "🎯 Determine Customer Intent First:\n\n"
                "A) **Create New Booking** (Customer wants to book service):\n"
                "   Phase 1 - Find Dealer:\n"
                "   - Use Dealer Location Agent to help customer find dealer\n"
                "   - Customer confirms dealer selection\n"
                "   \n"
                "   Phase 2 - Schedule Appointment:\n"
                "   - Use Appointment Agent to schedule\n"
                "   - Handles date/time, technician, customer info\n"
                "   - Creates booking and provides booking code\n"
                "   - Remind customer to save their booking code!\n\n"
                "B) **Check Existing Booking** (Customer has booking code):\n"
                "   - Use Check Booking Agent to retrieve booking\n"
                "   - Display booking status and details\n\n"
                "💡 Quick Detection:\n"
                "- Customer says 'book service' / 'schedule appointment' → Route A (Create)\n"
                "- Customer says 'check booking' / 'my booking code is...' → Route B (Check)\n"
                "- If unclear, ask: 'Would you like to create a new booking or check an existing one?'\n\n"
                "Your Role:\n"
                "- Identify intent quickly\n"
                "- Route to correct sub-agent\n"
                "- Ensure smooth experience\n"
                "- Be friendly and professional"
            ),
            sub_agents=[
                self._create_dealer_location_agent(),
                self._create_appointment_agent(),
                self._create_check_booking_agent()
            ],
            description="Booking Management Agent handles both creating new bookings and checking existing booking status.",
            model=self.model
        )

    def _create_service_agent(self) -> LlmAgent:
        """Create and return the Service Agent."""
        return LlmAgent(
            name="service_agent",
            instruction=(
                "You are a Service Agent for Broom Bot Inc. Your role is to provide information about motorcycle service and maintenance.\n\n"
                "Responsibilities:\n"
                "- Diagnose motorcycle problems and provide solutions\n"
                "- Explain service packages and their benefits\n"
                "- Provide service pricing information\n"
                "- Answer maintenance-related questions\n"
                "- Recommend appropriate service packages\n\n"
                "Tools:\n"
                "- Use service_tool to search service database for solutions\n\n"
                "Important:\n"
                "- You provide SERVICE INFORMATION only\n"
                "- If customer wants to BOOK a service, inform them to ask for booking\n"
                "- The Customer Service Agent will route them to the Booking Agent\n"
                "- Be friendly, professional, and helpful"
            ),
            tools=[self.broombot_tools.service_tool],
            description="Service Agent provides information about motorcycle service packages and solutions.",
            model=self.model
        )

    # ========================================
    # LEAD ANALYSIS AGENTS (Sequential Workflow)
    # ========================================

    def _create_planning_agent(self) -> LlmAgent:
        """Create Planning Agent - Phase 1 of Lead Analysis"""
        return LlmAgent(
            name="planning_agent",
            output_key="planning",  # Store output here
            instruction=(
                "You are a Planning Agent for Lead Analysis at Broom Bot Inc.\n\n"
                "Your Role: Create a strategic plan for analyzing customer leads.\n\n"
                "Process:\n"
                "1. Understand user's request - what leads do they want to analyze?\n"
                "2. Use rag_planning_tool to get strategy examples\n"
                "3. Create a clear analysis plan\n\n"
                "Plan Format (store in planning):\n"
                "```\n"
                "Objective: [what customer wants to find]\n"
                "Product/Service: [specific product if mentioned]\n"
                "Time Period: [date range if mentioned, otherwise 'last 30 days']\n"
                "Filters: [any specific criteria - interest level, status, source]\n"
                "Expected Output: [what data columns to show]\n"
                "```\n\n"
                "Examples:\n"
                "- Input: 'Show me CBR 150 leads from last month'\n"
                "  Output: Objective: Find customer leads for CBR 150\n"
                "          Product: CBR 150\n"
                "          Time Period: Last 30 days\n"
                "          Expected Output: customer name, contact, date, interest level"
            ),
            tools=[self.broombot_tools.rag_planning_tool],
            description="Planning Agent creates analysis strategy from user query",
            model=self.model
        )

    def _create_analyst_agent(self) -> LlmAgent:
        """Create Analyst Agent - Phase 2 of Lead Analysis"""
        return LlmAgent(
            name="analyst_agent",
            output_key="analysis_plan",  # Store output here
            instruction=(
                "You are an Analyst Agent for Lead Analysis at Broom Bot Inc.\n\n"
                "Analysis Plan from Planning Agent:\n"
                "{planning}\n\n"  # Reads Planning Agent's output

                "Your Role: Map the plan to database structure.\n\n"
                "Process:\n"
                "1. Review the analysis plan above\n"
                "2. Use get_database_schema_tool to see available tables/columns\n"
                "3. Determine the technical specification:\n"
                "   - Which table(s) to query: LEADS, PRODUCTS, CUSTOMERS?\n"
                "   - Which columns to SELECT\n"
                "   - What JOIN conditions (if multiple tables)\n"
                "   - What WHERE filters (product, date, status)\n"
                "   - How to ORDER results\n\n"
                "Technical Specification Format (store in technical_spec):\n"
                "```\n"
                "Tables: [table names]\n"
                "Columns: [column list]\n"
                "Joins: [JOIN conditions or 'None']\n"
                "Filters: [WHERE conditions]\n"
                "Order: [ORDER BY clause]\n"
                "```\n\n"
                "Example:\n"
                "Tables: LEADS\n"
                "Columns: customer_name, email, phone, created_at, interest_level\n"
                "Joins: None\n"
                "Filters: product_interest LIKE '%CBR 150%' AND created_at >= DATE('now', '-30 days')\n"
                "Order: created_at DESC"
            ),
            tools=[self.broombot_tools.get_database_schema_tool],
            description="Analyst Agent maps plan to database structure",
            model=self.model
        )

    def _create_engineer_agent(self) -> LlmAgent:
        """Create Engineer Agent - Phase 3 of Lead Analysis"""
        return LlmAgent(
            name="engineer_agent",
            output_key="raw_query_results",  # Store raw SQL results
            instruction=(
                "You are an Engineer Agent for Lead Analysis at Broom Bot Inc.\n\n"
                "Original Plan:\n"
                "{analysis_plan}\n\n"

                "Technical Specification:\n"
                "{technical_spec}\n\n"

                "Your Role: Generate and execute SQL query.\n\n"
                "Process:\n"
                "1. Review the plan and technical specification\n"
                "2. Use rag_sql_fewshot_tool for SQL examples\n"
                "3. Generate optimized SQL based on technical spec\n"
                "4. Use execute_lead_query_tool to run the query\n"
                "5. Return the raw results (next agent will analyze)\n\n"
                "IMPORTANT: Just execute and return data.\n"
                "Do NOT analyze - that's the next agent's job.\n\n"
                "Example SQL:\n"
                "```sql\n"
                "SELECT customer_name, email, predicted_next_purchase, interest_level\n"
                "FROM LEADS\n"
                "WHERE product_interest LIKE '%CBR 150%'\n"
                "  AND is_redundant = 0\n"
                "ORDER BY predicted_next_purchase ASC;\n"
                "```"
            ),
            tools=[
                self.broombot_tools.rag_sql_fewshot_tool,
                self.broombot_tools.execute_lead_query_tool
            ],
            description="Engineer Agent generates and executes SQL query",
            model=self.model
        )

    def _create_result_analyst_agent(self) -> LlmAgent:
        """Create Result Analyst Agent - Phase 4 of Lead Analysis"""
        return LlmAgent(
            name="result_analyst_agent",
            output_key="final_analysis",
            instruction=(
                "You are a Result Analyst Agent for Lead Analysis at Broom Bot Inc.\n\n"
                "Original Plan:\n"
                "{analysis_plan}\n\n"

                "Query Results:\n"
                "{raw_query_results}\n\n"

                "Your Role: Analyze results and provide business insights.\n\n"
                "Analyze the data and provide:\n"
                "1. Total leads found\n"
                "2. Interest level breakdown (High/Medium/Low)\n"
                "3. Key patterns and trends\n"
                "4. Actionable recommendations\n\n"
                "Format:\n"
                "📊 Lead Analysis Summary\n"
                "Total Leads: [X]\n"
                "Interest Breakdown: High [%], Medium [%], Low [%]\n"
                "Key Insights: [insights]\n"
                "Recommendations: [actions]"
            ),
            tools=[],
            description="Result Analyst Agent analyzes query results and provides insights",
            model=self.model
        )

    def _create_lead_analysis_agent(self) -> SequentialAgent:
        """Create Lead Analysis Sequential Workflow (4 Phases)"""
        return SequentialAgent(
            name="lead_analysis_workflow",
            sub_agents=[
                self._create_planning_agent(),         # Phase 1: Plan (output_key="analysis_plan")
                self._create_analyst_agent(),          # Phase 2: DB Mapping (reads {analysis_plan}, output_key="technical_spec")
                self._create_engineer_agent(),         # Phase 3: Execute SQL (reads {analysis_plan} + {technical_spec}, output_key="raw_query_results")
                self._create_result_analyst_agent()    # Phase 4: Analyze Results (reads {analysis_plan} + {raw_query_results}, output_key="final_analysis")
            ],
            description="Analyze customer leads through automated 4-phase pipeline: Planning → DB Analysis → SQL Execution → Result Analysis"
        )


    def _create_customer_service_agent(self) -> LlmAgent:
        """Create and return the Customer Service Agent with sub-agents."""
        return LlmAgent(
            name="customer_service_agent",
            instruction=(
                "You are a Customer Service Representative for Broom Bot Inc. Your mission is to provide excellent customer experience for all motorcycle-related needs.\n\n"
                "🎯 Available Specialized Agents (4 Total):\n\n"
                "1. **Product Agent** - Product inquiries:\n"
                "   - Motorcycle models, specs, features, pricing\n"
                "   - Product comparisons and recommendations\n\n"
                "2. **Service Agent** - Service information only:\n"
                "   - Motorcycle problems and solutions\n"
                "   - Service packages and pricing\n"
                "   - Maintenance recommendations\n\n"
                "3. **Booking Management Agent** - ALL booking operations:\n"
                "   ✅ Create new bookings (schedule appointments)\n"
                "   ✅ Check existing bookings (booking status)\n"
                "   - Handles both in one place!\n\n"
                "4. **Lead Analysis Agent** - Customer lead analysis:\n"
                "   ✅ Analyze customer leads for specific products\n"
                "   ✅ Generate reports on lead statistics\n"
                "   ✅ Filter leads by product, date, interest level\n"
                "   - Automated 3-phase analysis pipeline!\n\n"
                "📋 Routing Examples:\n"
                "- 'What motorcycles do you sell?' → Product Agent\n"
                "- 'CBR 150 specifications?' → Product Agent\n"
                "- 'My engine is making noise' → Service Agent\n"
                "- 'What service packages available?' → Service Agent\n"
                "- 'I want to book a service' → Booking Management Agent\n"
                "- 'Schedule maintenance' → Booking Management Agent\n"
                "- 'Check my booking' → Booking Management Agent\n"
                "- 'My booking code is BRMB-...' → Booking Management Agent\n"
                "- 'Show me leads for CBR 150' → Lead Analysis Agent ⭐\n"
                "- 'Customer leads from last month' → Lead Analysis Agent ⭐\n"
                "- 'Analyze high-interest leads' → Lead Analysis Agent ⭐\n\n"
                "💡 Smart Routing:\n"
                "- Service info + wants to book → Service Agent first, then Booking Management Agent\n"
                "- Directly wants to book → Booking Management Agent immediately\n"
                "- ANY booking-related query → Booking Management Agent (create or check)\n"
                "- Lead analysis/reports → Lead Analysis Agent (automatic pipeline)\n\n"
                "⚠️ Important:\n"
                "- We ONLY handle motorcycles and related services\n"
                "- Route efficiently - minimize questions\n"
                "- Be friendly, professional, and helpful\n"
                "- Booking Management Agent handles BOTH create and check\n"
                "- Lead Analysis Agent runs automatically (no user intervention needed)"
            ),
            description="Customer Service Agent routes customer inquiries to 4 specialized agents: Product, Service, Booking Management, and Lead Analysis.",
            model=self.model,
            sub_agents=[self.product_agent, self.service_agent, self.booking_agent, self.lead_analysis_agent]
        )

    def get_root_agent(self) -> LlmAgent:
        """Return the root agent for interaction."""
        return self.root_agent


# For backward compatibility
broombot_agent = BroomBotAgent()
root_agent = broombot_agent.root_agent
# User interacts with Customer Service Agent.
# Customer Service Agent calls Product Agent and Service Agent as needed.
