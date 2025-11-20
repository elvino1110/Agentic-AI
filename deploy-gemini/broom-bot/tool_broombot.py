from .embed_data import QdrantEmbedGemini
from .Database import BroomBotDatabase
from .LeadDatabase import LeadAnalysisDatabase


class BroomBotTools:
    """Class to manage BroomBot tools for product and service searches."""

    def __init__(self):
        """Initialize Qdrant embedding instances for service and product collections."""
        self.qdrant_service = QdrantEmbedGemini(collection_name="qdrant_data_service")
        self.qdrant_product = QdrantEmbedGemini(collection_name="qdrant_data_product")
        self.database = BroomBotDatabase()
        self.lead_database = LeadAnalysisDatabase()  # New: Lead Analysis Database

    def product_tool(self, query: str) -> str:
        """
        Search for motorcycle product information from the product database.

        Args:
            query: The search query for motorcycle products (e.g., "sport motorcycle", "Honda CBR specifications")
            ctx: Tool context from the agent

        Returns:
            str: Product information matching the query
        """
        try:
            results = self.qdrant_product.search(query, k=3)

            if not results:
                return "No product information found for your query."

            # Format the results
            formatted_results = []
            for i, res in enumerate(results, 1):
                formatted_results.append(f"{i}. {res.page_content}")

            return "\n\n".join(formatted_results)

        except Exception as e:
            return f"Error searching product database: {str(e)}"

    def service_tool(self, query: str) -> str:
        """
        Search for motorcycle service information from the service database.

        Args:
            query: The search query for motorcycle service issues (e.g., "engine problem", "brake repair")
            ctx: Tool context from the agent

        Returns:
            str: Service information matching the query
        """
        try:
            results = self.qdrant_service.search(query, k=3)

            if not results:
                return "No service information found for your query."

            # Format the results
            formatted_results = []
            for i, res in enumerate(results, 1):
                formatted_results.append(f"{i}. {res.page_content}")

            return "\n\n".join(formatted_results)

        except Exception as e:
            return f"Error searching service database: {str(e)}"
        
    def rag_sql_tool(self, question: str) -> str:
        """
        Search for the few shot query from question.

        Args:
            question: The input from user

        Returns:
            str: Few shot SQL query matching the question
        """

        try:
            results = self.qdrant_service.search(question, k=3)

            if not results:
                return "No dealer information found for your question."

            # Format the results
            formatted_results = []
            for i, res in enumerate(results, 1):
                formatted_results.append(f"{i}. {res.page_content}")

            return "\n\n".join(formatted_results)

        except Exception as e:
            return f"Error searching dealer database: {str(e)}"

    def find_dealer_location_tool(self, sql_query: str) -> str:
        """
        Find dealer locations based on the provided SQL query.

        Args:
            sql_query: The SQL query to find dealer locations (e.g., "SELECT * FROM Dealers WHERE city LIKE '%Jakarta%'")
            ctx: Tool context from the agent
        Returns:
            str: Dealer locations matching the SQL query
        """
        try:
            import sqlite3

            # Connect to the database
            conn = sqlite3.connect(self.database.db_name)
            cursor = conn.cursor()

            # Execute the SQL query
            cursor.execute(sql_query)
            results = cursor.fetchall()

            # Get column names
            column_names = [description[0] for description in cursor.description]

            conn.close()

            if not results:
                return "No dealer locations found matching your query."

            # Format the results
            formatted_results = []
            for i, row in enumerate(results, 1):
                dealer_info = f"Dealer {i}:\n"
                for col_name, value in zip(column_names, row):
                    dealer_info += f"  {col_name}: {value}\n"
                formatted_results.append(dealer_info)

            return "\n".join(formatted_results)

        except sqlite3.Error as e:
            return f"Database error: {str(e)}"
        except Exception as e:
            return f"Error executing query: {str(e)}"

    def get_today_date_tool(self) -> str:
        """
        Get today's date in YYYY-MM-DD format.

        Returns:
            str: Today's date
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

    def check_technician_availability_tool(self, dealer_name: str, start_time: str, end_time: str) -> str:
        """
        Check available technicians for a given dealer and time slot.

        Args:
            dealer_name: Name of the dealer
            start_time: Start time in YYYY-MM-DD HH:MM:SS format
            end_time: End time in YYYY-MM-DD HH:MM:SS format

        Returns:
            str: List of available technicians
        """
        try:
            result = self.database.check_available_technicians(dealer_name, start_time, end_time)
            return result
        except Exception as e:
            return f"Error checking technician availability: {str(e)}"

    def book_service_tool(self, customer_name: str, customer_plate_number: str, technician_name: str, dealer_name: str, start_time: str, end_time: str) -> str:
        """
        Book a service appointment.

        Args:
            customer_name: Customer's full name
            customer_plate_number: Customer's motorcycle plate number
            technician_name: Selected technician's name
            dealer_name: Name of the dealer
            start_time: Appointment start time in YYYY-MM-DD HH:MM:SS format
            end_time: Appointment end time in YYYY-MM-DD HH:MM:SS format

        Returns:
            str: Booking confirmation with booking code
        """
        try:
            result = self.database.insert_booking_from_tool(
                customer_name=customer_name,
                customer_plate_number=customer_plate_number,
                technician_name=technician_name,
                dealer_name=dealer_name,
                start_time=start_time,
                end_time=end_time
            )
            return result
        except Exception as e:
            return f"Error booking service: {str(e)}"

    def get_booking_tool(self, booking_code: str) -> str:
        """
        Retrieve booking information by booking code.

        Args:
            booking_code: The unique booking code (e.g., BRMB-1208-AB1234CD-1)

        Returns:
            str: Booking details or error message
        """
        try:
            result = self.database.get_booking(booking_code)

            if isinstance(result, dict):
                # Format the booking details nicely
                formatted = f"""Booking Details:
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    📋 Booking Code: {booking_code}
                    👤 Customer Name: {result['customer_name']}
                    🏍️  Plate Number: {result['customer_plate_number']}
                    📅 Start Time: {result['start_time']}
                    ⏰ End Time: {result['end_time']}
                    📊 Status: {result['status']}
                    🔧 Technician: {result['technician_name']}
                    🏢 Dealer: {result['dealer_name']}
                    📍 Dealer Address: {result['dealer_address']}
                    📞 Dealer Phone: {result['dealer_phone']}
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                """
                return formatted
            else:
                return result  # "No booking found" message
        except Exception as e:
            return f"Error retrieving booking: {str(e)}"

    # ========================================
    # LEAD ANALYSIS TOOLS
    # ========================================

    def rag_planning_tool(self, question: str) -> str:
        """
        Get planning strategy examples from RAG for lead analysis.

        Args:
            question: The planning question or user query

        Returns:
            str: Planning strategy examples and best practices
        """
        try:
            # Using existing Qdrant service collection for planning strategies
            # You can create a separate collection for planning if needed
            results = self.qdrant_service.search(question, k=2)

            if not results:
                return "No planning strategies found. Use default approach: identify product, time period, and customer filters."

            formatted_results = []
            for i, res in enumerate(results, 1):
                formatted_results.append(f"Strategy {i}: {res.page_content}")

            return "\n\n".join(formatted_results)

        except Exception as e:
            return f"Using default planning approach due to error: {str(e)}"

    def get_database_schema_tool(self) -> str:
        """
        Get database schema information for lead analysis.

        Returns:
            str: Database schema with tables and columns
        """
        try:
            schema = """
Database Schema for Lead Analysis (Predictive Lead Generation):

1. LEADS Table (Generated from Purchase Predictions):
   - id: INTEGER PRIMARY KEY
   - customer_name: TEXT
   - email: TEXT
   - phone: TEXT
   - product_interest: TEXT (predicted next purchase)
   - last_purchase_date: DATE
   - predicted_next_purchase: DATE (calculated from buying cycle)
   - purchase_distance_days: INTEGER (buying cycle)
   - interest_level: TEXT (High/Medium/Low based on proximity)
   - status: TEXT (New, Contacted, Qualified, Converted)
   - source: TEXT ('Predictive Analysis')
   - created_at: DATETIME
   - is_redundant: INTEGER (0=unique, 1=duplicate)

2. CUSTOMER_PROFILE_SALES Table (Purchase History):
   - id: INTEGER PRIMARY KEY
   - customer_name: TEXT
   - product_purchased: TEXT
   - purchase_date: DATE
   - purchase_amount: REAL
   - purchase_distance_days: INTEGER
   - average_buying_cycle_days: REAL
   - total_purchases: INTEGER

3. PRODUCTS Table:
   - id: INTEGER PRIMARY KEY
   - name: TEXT
   - category: TEXT
   - price: REAL

Common Queries:
- High-interest leads: WHERE interest_level = 'High' AND is_redundant = 0
- Product-specific: WHERE product_interest LIKE '%CBR%'
- Upcoming purchases: WHERE predicted_next_purchase <= DATE('now', '+30 days')
        """
            return schema

        except Exception as e:
            return f"Error retrieving schema: {str(e)}"

    def rag_sql_fewshot_tool(self, query_description: str) -> str:
        """
        Get few-shot SQL examples from RAG based on query description.

        Args:
            query_description: Description of the SQL query needed

        Returns:
            str: Similar SQL query examples
        """
        try:
            # Using rag_sql_tool logic for few-shot examples
            results = self.qdrant_service.search(query_description, k=2)

            if not results:
                return """Example SQL for lead analysis:

                    SELECT customer_name, email, created_at, interest_level
                    FROM LEADS
                    WHERE product_interest LIKE '%CBR%'
                    AND created_at >= DATE('now', '-30 days')
                    ORDER BY created_at DESC;
                """

            formatted_results = []
            for i, res in enumerate(results, 1):
                formatted_results.append(f"Example {i}:\n{res.page_content}")

            return "\n\n".join(formatted_results)

        except Exception as e:
            return f"Using default SQL template due to error: {str(e)}"

    def execute_lead_query_tool(self, sql_query: str) -> str:
        """
        Execute SQL query for lead analysis and return formatted results.

        Args:
            sql_query: The SQL query to execute

        Returns:
            str: Formatted query results
        """
        try:
            import sqlite3

            # Connect to LEAD ANALYSIS database (not booking database)
            conn = sqlite3.connect(self.lead_database.db_name)
            cursor = conn.cursor()

            # Execute query
            cursor.execute(sql_query)
            results = cursor.fetchall()

            # Get column names
            column_names = [description[0] for description in cursor.description]

            conn.close()

            if not results:
                return "No leads found matching the criteria."

            # Format results
            formatted = f"📊 Lead Analysis Results\n"
            formatted += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            formatted += f"Total Leads Found: {len(results)}\n\n"

            # Create table header
            header = " | ".join(column_names)
            formatted += f"{header}\n"
            formatted += "─" * len(header) + "\n"

            # Add rows (limit to first 20 for readability)
            for i, row in enumerate(results[:20], 1):
                row_data = " | ".join(str(val) for val in row)
                formatted += f"{row_data}\n"

            if len(results) > 20:
                formatted += f"\n... and {len(results) - 20} more results\n"

            formatted += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

            return formatted

        except sqlite3.Error as e:
            return f"Database error: {str(e)}"
        except Exception as e:
            return f"Error executing query: {str(e)}"


# Initialize the tools instance
# tools = BroomBotTools()
# product_tool = tools.product_tool
# service_tool = tools.service_tool
