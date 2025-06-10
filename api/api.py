from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import joblib
#from sklearn.preprocessing import StandardScaler
from typing import Dict, Tuple, Optional, Union
from flask_cors import CORS



app = Flask(__name__)
CORS(app)

class PCBuilder:
    def __init__(self):
        """Initialize the PC Builder with data loading and model setup"""
        self.df = self._load_data_and_model()
        self.min_build_cost = self._calculate_min_build_cost()
        self.use_case_info = self._initialize_use_cases()
        
    def _load_data_and_model(self) -> pd.DataFrame:
        """Load dataset and trained model with error handling"""
        try:
            df = pd.read_csv("preprocessed_output.csv")
            df["part"] = df["part"].str.lower().str.strip()
            
            # Load model and scaler
            self.model, self.scaler = joblib.load("pc_builder_model.pkl")
            
            # Prepare features
            features = ["price", "watt", "clock_speed", "vram", "core"]
            numeric_cols = features + ["performance_score"]
            
            # Convert and fill numeric columns
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
            
            # Predict performance scores if missing
            if "performance_score" not in df.columns or df["performance_score"].isnull().all():
                X = df[features].copy()
                X_scaled = self.scaler.transform(X)
                df["performance_score"] = self.model.predict(X_scaled)
                df["performance_score"] = df["performance_score"].clip(0, 100)
                
            return df.reset_index(drop=True)
            
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Required file not found: {e}")
        except Exception as e:
            raise RuntimeError(f"Error initializing PC Builder: {e}")
    
    def _calculate_min_build_cost(self) -> float:
        """Calculate minimum possible build cost across all required components"""
        required_parts = ["processor", "gpu", "ram", "motherboard", "psu", "ssd", "case"]
        return sum(self.df[self.df["part"] == part]["price"].min() for part in required_parts)
    
    def _initialize_use_cases(self) -> Dict:
        """Define use cases with allocation rules and component priorities"""
        return {
            "gaming": {
                "allocation": {"processor": 0.25, "gpu": 0.35, "ram": 0.15, 
                              "motherboard": 0.10, "psu": 0.05, "ssd": 0.05, "case": 0.05},
                "priority": ["gpu", "processor", "ram", "ssd", "motherboard", "psu", "case"]
            },
            "content creation": {
                "allocation": {"processor": 0.30, "gpu": 0.25, "ram": 0.20,
                             "motherboard": 0.10, "psu": 0.05, "ssd": 0.05, "case": 0.05},
                "priority": ["processor", "gpu", "ram", "ssd", "motherboard", "psu", "case"]
            },
            "3d rendering": {
                "allocation": {"processor": 0.35, "gpu": 0.30, "ram": 0.15,
                              "motherboard": 0.10, "psu": 0.05, "ssd": 0.03, "case": 0.02},
                "priority": ["processor", "gpu", "ram", "motherboard", "ssd", "psu", "case"]
            },
            "editing": {
                "allocation": {"processor": 0.30, "gpu": 0.30, "ram": 0.15,
                              "motherboard": 0.10, "psu": 0.05, "ssd": 0.05, "case": 0.05},
                "priority": ["processor", "gpu", "ram", "ssd", "motherboard", "psu", "case"]
            },
            "office/productivity": {
                "allocation": {"processor": 0.40, "gpu": 0.10, "ram": 0.15,
                              "motherboard": 0.10, "psu": 0.10, "ssd": 0.10, "case": 0.05},
                "priority": ["processor", "ram", "ssd", "motherboard", "psu", "gpu", "case"]
            },
            "general purpose": {
                "allocation": {"processor": 0.30, "gpu": 0.20, "ram": 0.20,
                              "motherboard": 0.10, "psu": 0.10, "ssd": 0.05, "case": 0.05},
                "priority": ["processor", "gpu", "ram", "motherboard", "psu", "ssd", "case"]
            }
        }
    
    def allocate_budget(self, use_case: str, budget: float) -> Dict[str, float]:
        """Allocate budget according to use case with minimum price constraints"""
        if use_case not in self.use_case_info:
            raise ValueError(f"Invalid use case. Choose from: {list(self.use_case_info.keys())}")
            
        if budget <= 0:
            raise ValueError("Budget must be positive")
            
        allocation_rules = self.use_case_info[use_case]["allocation"]
        
        # Calculate minimum required for each part
        min_prices = {part: self.df[self.df["part"] == part]["price"].min() 
                     for part in allocation_rules}
        total_min = sum(min_prices.values())
        
        if budget < total_min:
            raise ValueError(f"Budget too low. Minimum required: ₹{total_min:.2f}")
        
        # Calculate dynamic allocation respecting minimums
        adjusted_allocation = {}
        remaining_budget = budget - total_min
        
        for part, ratio in allocation_rules.items():
            min_amount = min_prices[part]
            allocated = min_amount + (ratio * remaining_budget)
            adjusted_allocation[part] = allocated
        
        return adjusted_allocation
    
    def select_component(self, part: str, max_price: float, 
                        performance_weight: float = 0.7, 
                        price_weight: float = 0.3) -> Optional[pd.Series]:
        """Select optimal component based on performance and price balance"""
        options = self.df[self.df["part"] == part].copy()
        if options.empty:
            return None
            
        # Filter affordable options
        options = options[options["price"] <= max_price]
        if options.empty:
            return None
            
        # Normalize scores (0-1 range)
        options["norm_perf"] = (options["performance_score"] - options["performance_score"].min()) / \
                             (options["performance_score"].max() - options["performance_score"].min() + 1e-9)
        options["norm_price"] = 1 - ((options["price"] - options["price"].min()) / \
                                  (options["price"].max() - options["price"].min() + 1e-9))
        
        # Combined score with weights
        options["score"] = (performance_weight * options["norm_perf"] + 
                          price_weight * options["norm_price"])
        
        # Select top 3 and pick randomly for variety (weighted by score)
        top_options = options.nlargest(5, "score")
        if len(top_options) > 1:
            probs = top_options["score"] / top_options["score"].sum()
            return top_options.sample(1, weights=probs).iloc[0]
        return top_options.iloc[0] if not top_options.empty else None
    
    def optimize_build(self, budget: float, use_case: str) -> Tuple[Dict, float]:
        """Optimize PC build for given budget and use case"""
        try:
            allocation = self.allocate_budget(use_case, budget)
        except ValueError as e:
            return None, str(e)
            
        selected = {}
        remaining = budget
        
        # First pass - select components in priority order
        priority_order = self.use_case_info[use_case]["priority"]
        for part in priority_order:
            if part not in allocation:
                continue
                
            component = self.select_component(part, min(allocation[part], remaining))
            if component is not None:
                selected[part] = component
                remaining -= component["price"]
        
        # Second pass - upgrade components with remaining budget
        for part in priority_order:
            if part not in selected:
                continue
                
            current_price = selected[part]["price"]
            upgrade_budget = current_price + remaining
            upgrade = self.select_component(part, upgrade_budget)
            
            if upgrade is not None and upgrade["price"] > current_price:
                remaining += (selected[part]["price"] - upgrade["price"])
                selected[part] = upgrade
                if remaining <= 0:
                    break
        
        # Ensure all required parts are selected
        required_parts = set(self.use_case_info[use_case]["allocation"].keys())
        missing_parts = required_parts - set(selected.keys())
        
        for part in missing_parts:
            component = self.select_component(part, remaining)
            if component is not None:
                selected[part] = component
                remaining -= component["price"]
        
        return selected, max(0, remaining)
    
    def format_build_response(self, build: Dict, remaining: float) -> Dict:
        """Format the build for API response"""
        if not build:
            return {"error": "Could not build a PC within this budget"}
            
        response = {
            "components": [],
            "total_cost": 0,
            "remaining_budget": remaining,
            "total_performance": 0
        }
        
        for part, component in build.items():
            comp_data = {
                "part": part,
                "name": component["name"],
                "price": float(component["price"]),
                "performance_score": float(component["performance_score"])
            }
            response["components"].append(comp_data)
            response["total_cost"] += component["price"]
            response["total_performance"] += component["performance_score"]
        
        response["total_cost"] = float(response["total_cost"])
        response["total_performance"] = float(response["total_performance"])
        
        return response

# Initialize the PCBuilder when the API starts
try:
    pc_builder = PCBuilder()
except Exception as e:
    print(f"Failed to initialize PCBuilder: {e}")
    pc_builder = None

@app.route('/build-pc', methods=['GET'])
def build_pc():
    print("here")
    """Endpoint to get PC build recommendations"""
    if pc_builder is None:
        print("error is here")
        return jsonify({"error": "PC Builder service is not available"}), 500
    
    # Get parameters from query string
    budget = request.args.get('budget', type=float)
    use_case = request.args.get('use_case', default='general purpose')

    print(budget, use_case)
    
    if budget is None:
        return jsonify({"error": "Budget parameter is required"}), 400
    
    try:
        build, remaining = pc_builder.optimize_build(budget, use_case.lower())
        if isinstance(remaining, str):  # This means there was an error
            return jsonify({"error": remaining}), 400
            
        response = pc_builder.format_build_response(build, remaining)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)