"""
FolliCare Model Context Protocol (MCP) Server (JSON-RPC 2.0 Standard).
Provides external LLM assistants and tools with structured access to:
1. Hair Science & Trichology Knowledge Base
2. Step-by-Step Hair Routine Recommendations
3. Product Catalog & Inventory Resources
4. Git React Code Push & UI Synchronization Tool
"""

import sys
import json
import logging
from typing import Dict, Any, List, Optional
from data.database import get_database
from rag.vector_store import get_vector_store
from agents.git_sync_agent import get_git_sync_agent

logger = logging.getLogger("FolliCareMCPServer")

class FolliCareMCPServer:
    """
    Implements the Model Context Protocol (MCP) specification over JSON-RPC 2.0.
    """
    def __init__(self):
        self.server_name = "follicare-cosmetics-mcp"
        self.server_version = "1.0.0"
        self.db = get_database()
        self.vector_store = get_vector_store()
        self.git_sync_agent = get_git_sync_agent()

    def get_server_info(self) -> Dict[str, Any]:
        return {
            "name": self.server_name,
            "version": self.server_version,
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True
            }
        }

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "search_hair_knowledge",
                "description": "Searches the FolliCare clinical trichology and hair science knowledge base.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The hair problem, ingredient name, or clinical question."
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of relevant knowledge chunks to retrieve (default: 3).",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "recommend_hair_routine",
                "description": "Generates a structured multi-step hair care routine (Cleanse, Treat, Nourish) based on specific hair concerns.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "hairConcern": {
                            "type": "string",
                            "description": "The primary hair or scalp concern (e.g. 'Hair Fall & Thinning', 'Dandruff & Scalp Itch', 'Damaged & Dry Hair', 'Oily Scalp & Limp Hair')."
                        }
                    },
                    "required": ["hairConcern"]
                }
            },
            {
                "name": "git_push_react_code",
                "description": "Stages complete React 18 frontend codebase, creates or switches to specified branch, and pushes code to GitHub remote repository.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "branch": {
                            "type": "string",
                            "description": "Target Git branch name (default: 'react-ui-sync').",
                            "default": "react-ui-sync"
                        },
                        "commitMessage": {
                            "type": "string",
                            "description": "Git commit message describing UI updates."
                        },
                        "remoteUrl": {
                            "type": "string",
                            "description": "Optional GitHub remote repository URL (defaults to user GitHub or current origin)."
                        }
                    }
                }
            },
            {
                "name": "query_product_inventory",
                "description": "Queries product inventory status, stock level, ratings, and price.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Product category filter (e.g. 'Scalp Care', 'Shampoo', 'Serum', 'Mask')."
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price in USD."
                        }
                    }
                }
            }
        ]

    def get_resources_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "uri": "follicare://catalog",
                "name": "FolliCare Product Catalog",
                "description": "Real-time list of all active FolliCare hair care products and formulas.",
                "mimeType": "application/json"
            },
            {
                "uri": "follicare://clinical_studies",
                "name": "FolliCare Trichology Clinical Knowledge",
                "description": "Clinical studies, active ingredient profiles, and trichological guidelines.",
                "mimeType": "application/json"
            }
        ]

    def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an MCP tool by name and returns standard MCP content response.
        """
        if name == "search_hair_knowledge":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 3)
            results = self.vector_store.search(query, top_k=top_k)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "query": query,
                            "results_count": len(results),
                            "results": results
                        }, indent=2)
                    }
                ]
            }

        elif name == "recommend_hair_routine":
            concern = arguments.get("hairConcern", "Hair Fall & Thinning")
            routines = {
                "Hair Fall & Thinning": {
                    "hairConcern": "Hair Fall & Thinning",
                    "step1_cleanse": {
                        "action": "Cleanse Scalp & Activate Microcirculation",
                        "product": "Rosemary Scalp Density Cleanser",
                        "usage": "Massage into wet scalp for 2 minutes with fingertips to stimulate blood flow."
                    },
                    "step2_treat": {
                        "action": "Follicle Stimulation Treatment",
                        "product": "3% Redensyl + Procapil Scalp Serum",
                        "usage": "Apply 1-2 droppers directly along part lines onto dry or towel-dried scalp at bedtime."
                    },
                    "step3_nourish": {
                        "action": "Density Support & Fiber Fortification",
                        "product": "Biotin Fortifying Conditioner",
                        "usage": "Distribute from mid-lengths to ends; leave on for 3 minutes before rinsing."
                    },
                    "frequency": "Daily cleanser & serum; conditioner with every wash."
                },
                "Damaged & Dry Hair": {
                    "hairConcern": "Damaged & Dry Hair",
                    "step1_cleanse": {
                        "action": "Gentle Sulfate-Free Moisture Wash",
                        "product": "Hydra-Ceramide Recovery Shampoo",
                        "usage": "Gently massage into hair and scalp, producing creamy lather."
                    },
                    "step2_treat": {
                        "action": "Lipid & Protein Cuticle Repair",
                        "product": "Deep Keratin Reconstruction Mask",
                        "usage": "Apply lavishly to mid-lengths and ends once or twice weekly for 10 minutes."
                    },
                    "step3_nourish": {
                        "action": "Leave-In Heat & Environmental Shield",
                        "product": "Argan & Marula Gloss Infusion Oil",
                        "usage": "Apply 2-3 drops through damp ends before heat styling or drying."
                    },
                    "frequency": "2-3 times weekly."
                },
                "Dandruff & Scalp Itch": {
                    "hairConcern": "Dandruff & Scalp Itch",
                    "step1_cleanse": {
                        "action": "Anti-Microbial & Exfoliating Wash",
                        "product": "Tea Tree & Salicylic Acid Clarifying Shampoo",
                        "usage": "Lather into scalp; allow salicylic acid to sit for 3 minutes to dissolve sebum plugs."
                    },
                    "step2_treat": {
                        "action": "Scalp Microbiome Soothing Tonic",
                        "product": "Niacinamide + Zinc PCA Balancing Scalp Mist",
                        "usage": "Spray directly onto irritated scalp sections post-wash."
                    },
                    "step3_nourish": {
                        "action": "Weightless Hydration",
                        "product": "Aloe & Hyaluronic Weightless Conditioner",
                        "usage": "Keep away from roots; focus on hair ends."
                    },
                    "frequency": "Use anti-dandruff shampoo 2-3x weekly until flaking resolves."
                },
                "Oily Scalp & Limp Hair": {
                    "hairConcern": "Oily Scalp & Limp Hair",
                    "step1_cleanse": {
                        "action": "Sebum Regulating Cleanse",
                        "product": "Clarifying Apple Cider Vinegar & Clay Shampoo",
                        "usage": "Target scalp roots with lukewarm water."
                    },
                    "step2_treat": {
                        "action": "Root Lift & Follicle Rebalance",
                        "product": "Peppermint Volumizing Root Spray",
                        "usage": "Spray at towel-dried roots before blow-drying."
                    },
                    "step3_nourish": {
                        "action": "Featherlight Ends Hydration",
                        "product": "Silk Protein Light Leave-In Mist",
                        "usage": "Lightly mist ends only."
                    },
                    "frequency": "Wash every 1-2 days as needed."
                }
            }

            routine = routines.get(concern, routines["Hair Fall & Thinning"])
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(routine, indent=2)
                    }
                ]
            }

        elif name == "git_push_react_code":
            branch = arguments.get("branch", "react-ui-sync")
            commit_msg = arguments.get("commitMessage")
            remote_url = arguments.get("remoteUrl")
            res = self.git_sync_agent.sync_and_push(
                branch_name=branch,
                commit_message=commit_msg,
                remote_url=remote_url
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(res, indent=2)
                    }
                ]
            }

        elif name == "query_product_inventory":
            cat = arguments.get("category")
            max_p = arguments.get("max_price")
            products = self.db.get_all_products()
            if cat:
                products = [p for p in products if cat.lower() in p.get("category", "").lower()]
            if max_p is not None:
                products = [p for p in products if p.get("price", 0) <= float(max_p)]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "matched_count": len(products),
                            "products": products
                        }, indent=2)
                    }
                ]
            }

        else:
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Unknown tool '{name}'."
                    }
                ]
            }

    def handle_read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Reads an MCP resource by URI.
        """
        if uri == "follicare://catalog":
            products = self.db.get_all_products()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(products, indent=2)
                    }
                ]
            }
        elif uri == "follicare://clinical_studies":
            docs = self.vector_store.documents
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(docs, indent=2)
                    }
                ]
            }
        else:
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": f"Resource not found: {uri}"
                    }
                ]
            }

    def process_json_rpc(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes standard JSON-RPC 2.0 messages.
        """
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": self.get_server_info(),
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False}
                    }
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": self.get_tools_definition()
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            call_result = self.handle_call_tool(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": call_result
            }

        elif method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "resources": self.get_resources_definition()
                }
            }

        elif method == "resources/read":
            uri = params.get("uri", "")
            read_result = self.handle_read_resource(uri)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": read_result
            }

        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found."
                }
            }

    def run_stdio_server(self):
        """
        Runs the MCP server over standard input/output (STDIO) for integration with LLM CLI tools.
        """
        logger.info("FolliCare MCP JSON-RPC 2.0 Server listening on STDIO...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.process_json_rpc(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as ex:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(ex)}"
                    }
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()

if __name__ == "__main__":
    server = FolliCareMCPServer()
    server.run_stdio_server()
