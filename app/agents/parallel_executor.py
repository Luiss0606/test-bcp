"""Parallel execution of financial analysis agents."""

import asyncio
from typing import Dict, Any, List, Tuple
from langchain_core.runnables import RunnableParallel, RunnableLambda
from .base_agent import MinimumPaymentAgent, OptimizedPaymentAgent, ConsolidationAgent


class ParallelAgentExecutor:
    """Executes multiple financial analysis agents in parallel."""
    
    def __init__(self):
        # Initialize the three specialized agents
        self.minimum_agent = MinimumPaymentAgent()
        self.optimized_agent = OptimizedPaymentAgent()
        self.consolidation_agent = ConsolidationAgent()
        
        # Create wrapper functions that extract the right data for each agent
        def format_minimum_input(data):
            scenarios = data.get("scenarios", {})
            customer_info = data.get("customer_info", {})
            if "minimum" in scenarios:
                formatted_data = {
                    "scenario": scenarios["minimum"],
                    "customer_info": customer_info
                }
                return {"input": self.minimum_agent._format_scenario_data(formatted_data)}
            return {"input": "No minimum scenario data available"}
        
        def format_optimized_input(data):
            scenarios = data.get("scenarios", {})
            customer_info = data.get("customer_info", {})
            if "optimized" in scenarios:
                formatted_data = {
                    "scenario": scenarios["optimized"],
                    "customer_info": customer_info
                }
                return {"input": self.optimized_agent._format_scenario_data(formatted_data)}
            return {"input": "No optimized scenario data available"}
        
        def format_consolidation_input(data):
            scenarios = data.get("scenarios", {})
            customer_info = data.get("customer_info", {})
            if "consolidation" in scenarios:
                formatted_data = {
                    "scenario": scenarios["consolidation"],
                    "customer_info": customer_info
                }
                return {"input": self.consolidation_agent._format_scenario_data(formatted_data)}
            return {"input": "No consolidation scenario data available"}
        
        # Create parallel runnable with proper input formatting
        self.parallel_agents = RunnableParallel({
            "minimum_analysis": RunnableLambda(format_minimum_input) | self.minimum_agent.chain,
            "optimized_analysis": RunnableLambda(format_optimized_input) | self.optimized_agent.chain,
            "consolidation_analysis": RunnableLambda(format_consolidation_input) | self.consolidation_agent.chain
        })
    
    async def execute_parallel_analysis(
        self, 
        scenarios: Dict[str, Any], 
        customer_info: Dict[str, Any]
    ) -> Dict[str, str]:
        """Execute all three agents in parallel."""
        
        # Prepare input data - now all agents get the same input structure
        input_data = {
            "scenarios": scenarios,
            "customer_info": customer_info
        }
        
        try:
            # Execute all agents in parallel
            results = await self.parallel_agents.ainvoke(input_data)
            
            # Extract content from responses
            processed_results = {}
            for key, result in results.items():
                if hasattr(result, 'content'):
                    processed_results[key] = result.content
                else:
                    processed_results[key] = str(result)
            
            return processed_results
            
        except Exception as e:
            return {
                "error": f"Error en la ejecución paralela de agentes: {str(e)}",
                "minimum_analysis": "Error en análisis de pago mínimo",
                "optimized_analysis": "Error en análisis optimizado", 
                "consolidation_analysis": "Error en análisis de consolidación"
            }
    
    async def execute_individual_analysis(
        self,
        scenario_type: str,
        scenario_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> str:
        """Execute a single agent analysis."""
        
        data = {
            "scenario": scenario_data,
            "customer_info": customer_info
        }
        
        if scenario_type == "minimum":
            return await self.minimum_agent.analyze(data)
        elif scenario_type == "optimized":
            return await self.optimized_agent.analyze(data)
        elif scenario_type == "consolidation":
            return await self.consolidation_agent.analyze(data)
        else:
            return f"Tipo de escenario no reconocido: {scenario_type}"


class AgentOrchestrator:
    """Orchestrates the parallel execution and result consolidation."""
    
    def __init__(self):
        self.executor = ParallelAgentExecutor()
    
    async def run_complete_analysis(
        self,
        customer_id: str,
        scenarios: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run complete analysis with all agents and consolidate results."""
        
        # Execute parallel analysis
        agent_results = await self.executor.execute_parallel_analysis(
            scenarios, customer_info
        )
        
        # Prepare consolidated response
        analysis_result = {
            "customer_id": customer_id,
            "timestamp": "2024-01-01T00:00:00Z",  # Will be set by API
            "scenarios": scenarios,
            "agent_analyses": agent_results,
            "summary": self._create_summary(scenarios, agent_results),
            "recommendations": self._create_recommendations(scenarios, agent_results)
        }
        
        return analysis_result
    
    def _create_summary(
        self, 
        scenarios: Dict[str, Any], 
        agent_results: Dict[str, str]
    ) -> str:
        """Create a summary of all scenarios."""
        
        summary_parts = []
        
        # Extract key metrics
        if "minimum" in scenarios:
            min_scenario = scenarios["minimum"]
            summary_parts.append(
                f"Pago Mínimo: ${min_scenario.get('total_monthly_payment', 0):,.2f}/mes, "
                f"{min_scenario.get('total_payoff_months', 0)} meses, "
                f"${min_scenario.get('total_interest', 0):,.2f} en intereses"
            )
        
        if "optimized" in scenarios:
            opt_scenario = scenarios["optimized"]
            summary_parts.append(
                f"Plan Optimizado: ${opt_scenario.get('total_monthly_payment', 0):,.2f}/mes, "
                f"{opt_scenario.get('total_payoff_months', 0)} meses, "
                f"Ahorro: ${opt_scenario.get('savings_vs_minimum', 0):,.2f}"
            )
        
        if "consolidation" in scenarios:
            cons_scenario = scenarios["consolidation"]
            summary_parts.append(
                f"Consolidación: ${cons_scenario.get('total_monthly_payment', 0):,.2f}/mes, "
                f"Ahorro: ${cons_scenario.get('savings_vs_minimum', 0):,.2f}"
            )
        
        return " | ".join(summary_parts)
    
    def _create_recommendations(
        self,
        scenarios: Dict[str, Any],
        agent_results: Dict[str, str]
    ) -> str:
        """Create general recommendations based on all scenarios."""
        
        recommendations = []
        
        # Find best scenario by savings
        best_scenario = None
        max_savings = 0
        
        for scenario_name, scenario in scenarios.items():
            savings = scenario.get('savings_vs_minimum', 0)
            if savings > max_savings:
                max_savings = savings
                best_scenario = scenario_name
        
        if best_scenario:
            if best_scenario == "optimized":
                recommendations.append(
                    "Recomendación principal: Implementar el plan optimizado para "
                    f"ahorrar ${max_savings:,.2f} en intereses."
                )
            elif best_scenario == "consolidation":
                recommendations.append(
                    "Recomendación principal: Considerar la consolidación de deudas "
                    f"para ahorrar ${max_savings:,.2f} en intereses."
                )
        
        recommendations.append(
            "Evitar pagar solo los mínimos para reducir el costo total de las deudas."
        )
        
        return " ".join(recommendations)
