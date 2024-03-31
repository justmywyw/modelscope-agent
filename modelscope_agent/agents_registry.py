from typing import List, Union

# import ray
from modelscope_agent.agent import Agent
from modelscope_agent.environment import Environment
from ray.util.client.common import ClientActorHandle


class AgentRegistry:

    def __init__(self, remote=True, **kwargs):
        self._agents = {}
        self._agents_state = {}
        self.remote = remote

    def register_agent(self,
                       agent: Union[Agent, ClientActorHandle],
                       env_context: Environment = None):
        """
        Add an agent to the register center
        Args:
            agent: Agent object
            env_context: Env context that need to pass to agent
        Returns: None

        """
        if isinstance(agent, Agent):
            role = agent.role()
        else:
            role = ray.get(agent.role.remote())
        self._agents[role] = agent
        self._agents_state[role] = True

        # set up the env_context
        if env_context:
            if isinstance(agent, Agent):
                agent.set_env_context(env_context)
            else:
                ray.get(agent.set_env_context.remote(env_context))

    def get_agents_by_role(self, roles: list) -> List:
        agents = {}
        for role in roles:
            agents[role] = self.get_agent_by_role(role)
        return agents

    def get_agent_by_role(self, role: str) -> Agent:
        return self._agents.get(role)

    def get_all_role(self):
        return self._agents

    def get_available_role_name(self):

        return [role for role, state in self._agents_state.items() if state]

    def get_user_agents_role_name(self, agents: List[Agent] = None):
        if not agents:
            agents = self._agents.values()
        if self.remote:
            return [
                ray.get(agent.role.remote()) for agent in agents
                if ray.get(agent.is_user_agent.remote())
            ]
        else:
            return [agent.role() for agent in agents if agent.is_user_agent()]

    def set_user_agent(self, role: str, human_input_mode: str = 'ON'):
        agent = self._agents.get(role)
        if agent:
            if self.remote:
                ray.get(agent.set_human_input_mode.remote(human_input_mode))
            else:
                agent.set_human_input_mode(human_input_mode)

    def unset_user_agent(self, role: str):
        agent = self._agents.get(role)
        if agent:
            if self.remote:
                ray.get(agent.set_human_input_mode.remote('CLOSE'))
            else:
                agent.set_human_input_mode('CLOSE')

    def register_agents(self,
                        agents: List[Agent],
                        env_context: Environment = None):
        """
        Add a list of agents to the environment
        Args:
            agents: list of agent object
            env_context: environment context that need to pass to agent

        Returns: None

        """
        if len(agents) == 0:
            return
        for item in agents:
            self.register_agent(item, env_context)
