from .embed_data import QdrantEmbedGemini
from .Database import BroomBotDatabase


class BroomBotTools:
    """Class to manage BroomBot tools for product and service searches."""

    def __init__(self):
        """Initialize Qdrant embedding instances for service and product collections."""
        self.qdrant_service = QdrantEmbedGemini(collection_name="qdrant_data_service")
        self.qdrant_product = QdrantEmbedGemini(collection_name="qdrant_data_product")
        self.database = BroomBotDatabase()

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
🔧 Technician ID: {result['id_technician']}
🏢 Dealer ID: {result['id_dealer']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                return formatted
            else:
                return result  # "No booking found" message
        except Exception as e:
            return f"Error retrieving booking: {str(e)}"


# Initialize the tools instance
# tools = BroomBotTools()
# product_tool = tools.product_tool
# service_tool = tools.service_tool
