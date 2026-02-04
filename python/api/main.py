from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Import simulation functions from the main sim package
import sys
import os
# Add the parent directory to the system path to allow importing from 'sim'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../python')))

from sim import test_characters, parse_levels
from collections import defaultdict
from util.log import log


app = FastAPI()

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationRequest(BaseModel):
    characters: List[str]
    levels: str
    num_rounds: int = 5
    num_fights: int = 3
    iterations: int = 500
    debug: bool = False
    monster: str = "generic"

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/simulate")
async def simulate_combat(request: SimulationRequest):
    try:
        start_level, end_level = parse_levels(request.levels)
        
        # Temporarily enable log for this request if debug is true
        if request.debug:
            log.enable()
        else:
            # Ensure log is disabled for non-debug runs to prevent unintended accumulation
            log.enabled = False
            # Clear any residual logs from previous debug runs
            log.record_.clear()

        dpr_results, aggregated_log_data = test_characters(
            characters=request.characters,
            start_level=start_level,
            end_level=end_level,
            num_rounds=request.num_rounds,
            num_fights=request.num_fights,
            iterations=request.iterations,
            debug=request.debug,
            monster_name=request.monster,
        )
        
        response_content = {"dpr_results": dpr_results}
        if request.debug and aggregated_log_data:
            # Convert defaultdict to a regular dict for JSON serialization
            response_content["debug_log"] = dict(aggregated_log_data)
        
        return response_content

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")