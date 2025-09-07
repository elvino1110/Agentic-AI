from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevToolw
from typing import List

@CrewBase
class FinancialResearcher():
    """FinancialResearcher crew"""

    # agents: List[BaseAgent]
    # tasks: List[Task]
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'], verbose=True, tools=[SerperDevTool()])
    
    @agent
    def analyst(self) -> Agent:
        return Agent(config=self.agents_config['analyst'], verbose=True)

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])

    @task
    def analysis_task(self) -> Task:
        return Task(config=self.tasks_config['analysis_task'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            processes=Process.sequential,
            verbose=True
        )