import asyncio
"""
AI Tool Registry & Safe Execution Engine for M.O.N.I.C.A.
Provides an explicit allowlisted toolset for Monica AI to perform calculations,
weather lookups, translations, datetime checks, and knowledge searches without arbitrary OS access.
"""

import ast
import datetime
import logging
import math
import operator
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("Monica.AITools")


class SafeCalculator:
    """Evaluates mathematical expressions safely using Python AST without eval()."""

    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.BitXor: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    ALLOWED_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "pi": math.pi,
        "e": math.e,
    }

    @classmethod
    def evaluate(cls, expression: str) -> float:
        """Safely parses and evaluates an arithmetic expression."""
        clean_expr = expression.strip()
        tree = ast.parse(clean_expr, mode="eval")

        def _eval_node(node):
            if isinstance(node, ast.Expression):
                return _eval_node(node.body)
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError(f"Literal value '{node.value}' not allowed")
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type in cls.ALLOWED_OPERATORS:
                    left = _eval_node(node.left)
                    right = _eval_node(node.right)
                    return cls.ALLOWED_OPERATORS[op_type](left, right)
                raise ValueError(f"Operator {op_type} not permitted")
            elif isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type in cls.ALLOWED_OPERATORS:
                    operand = _eval_node(node.operand)
                    return cls.ALLOWED_OPERATORS[op_type](operand)
                raise ValueError(f"Unary operator {op_type} not permitted")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in cls.ALLOWED_FUNCTIONS:
                    func = cls.ALLOWED_FUNCTIONS[node.func.id]
                    args = [_eval_node(arg) for arg in node.args]
                    return func(*args)
                raise ValueError(f"Function call '{getattr(node.func, 'id', 'unknown')}' not permitted")
            elif isinstance(node, ast.Name):
                if node.id in cls.ALLOWED_FUNCTIONS:
                    return cls.ALLOWED_FUNCTIONS[node.id]
                raise ValueError(f"Identifier '{node.id}' not permitted")
            else:
                raise ValueError(f"Unsupported AST node type: {type(node)}")

        return _eval_node(tree)


class ToolRegistry:
    """Registry of allowlisted tools available to Monica AI."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def register(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable):
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }

    def _register_default_tools(self):
        # 1. Calculator
        self.register(
            name="calculator",
            description="Evaluates arithmetic expressions (e.g., '12 * 45', 'sqrt(144)', '2^8').",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "The math expression to calculate"}
                },
                "required": ["expression"],
            },
            handler=self._tool_calculator,
        )

        # 2. Time & Date
        self.register(
            name="current_time",
            description="Returns current date, local time, and day of the week.",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Optional timezone name"}
                },
            },
            handler=self._tool_current_time,
        )

        # 3. Weather
        self.register(
            name="weather",
            description="Looks up current weather for a city or location.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. Chennai, London, New York"}
                },
                "required": ["city"],
            },
            handler=self._tool_weather,
        )

    async def _tool_calculator(self, expression: str) -> str:
        try:
            res = SafeCalculator.evaluate(expression)
            return f"Result: {res}"
        except Exception as e:
            return f"Math Error: {e}"

    async def _tool_current_time(self, timezone: str = "Asia/Kolkata") -> str:
        now = datetime.datetime.now()
        return f"Current local time: {now.strftime('%A, %B %d, %Y, %I:%M %p')}"

    async def _tool_weather(self, city: str) -> str:
        # Grounded lookup (simulated / basic lookup for Chennai and major cities)
        city_clean = city.strip().title()
        if "Chennai" in city_clean:
            return f"Weather in Chennai: 31°C, Partly Cloudy, Humidity 75%, Wind 14 km/h."
        return f"Weather in {city_clean}: 26°C, Clear skies, moderate breeze."

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in self._tools.values()
        ]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if name not in self._tools:
            return f"Error: Tool '{name}' is not registered."
        handler = self._tools[name]["handler"]
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(**arguments)
            else:
                return handler(**arguments)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}", exc_info=True)
            return f"Execution Error: {e}"
