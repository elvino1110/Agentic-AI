from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from email_agent import email_agent
import asyncio

class ResearchManager:
    async def run(self, query: str):
        """Run the deep research process, yeilding the status updates and final report"""

        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            
            print(f"View trace: https://platform.openai.com/traces/{trace_id}")
            yield f"View trace: https://platform.openai.com/traces/{trace_id}"
            print("Starting research process...")
            
            search_plan = await self.plan_searhes(query)
            yield "Search planned, starting to search..."

            search_results = await self.perform_searches(search_plan)
            yield "Searches completed, starting to write report..."

            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."

            await self.send_email(report)
            yield "Email sent successfully! Research complete."

            yield report.markdown_report

    async def plan_searhes(self, query: str) -> WebSearchPlan:
        """Plan the searches to perform based on the query."""
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches.")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Perform the searches to perform for the query"""

        print("Performing searches...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(search_item)) for search_item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed.")
        print("All searches completed.")
        return results

    async def search(self, search_item: WebSearchItem) -> str | None:
        """Perform a search for the query"""

        input = f"Search term: {search_item.query}\nReason for searching: {search_item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception as e:
            return None
        
    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Write the report for the query"""
        print("Thinking about the report...")
        input = f"Original query: {query}\n Summarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData) -> None:
        """Send the email with the report"""
        print("Sending email...")
        await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent successfully!")
        return report