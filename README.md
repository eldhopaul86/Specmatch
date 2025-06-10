# 🧠 AI-Powered PC Spec Recommender - **SpecMatch**

## 🔍 Overview

**SpecMatch** is an intelligent web-based tool that recommends the **best PC configurations** based on the user's **budget** and **intended usage** (e.g., gaming, video editing, office work). It combines **Machine Learning** and **Optimization Algorithms** to suggest cost-effective and performance-optimized hardware combinations like CPU, GPU, RAM, Storage, etc.

## ✨ Features

* 💸 **Budget-Aware PC Suggestions**
* 🎯 **Purpose-Specific Recommendations** (Gaming, Editing, Office Work)
* 🧠 **ML-Powered Component Prediction**
* 🧬 **Optimization Engine** using Random Forest / Genetic Algorithm
* 🌐 **Simple, User-Friendly Web Interface**

## 🛠 Tech Stack

* **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
* **Backend**: Python (Flask)
* **Machine Learning**: Scikit-learn, PyTorch
* **Database**: MongoDB
* **Optimization**: Random Forest, Genetic Algorithm (optional)

## 🚀 How It Works

1. **User Inputs**:

   * Enters **budget** (e.g., ₹60,000)
   * Selects **usage purpose** (e.g., Gaming)
2. **AI Model Predicts**:

   * Uses trained **ML models** to estimate required performance benchmarks
3. **Optimizer Suggests Best Components**:

   * Finds the best mix of CPU, GPU, RAM, etc. within the budget using optimization algorithms
4. **Output Displayed**:

   * Final PC build is shown including:

     * CPU
     * GPU
     * RAM
     * Storage
     * Motherboard
     * PSU

## 📦 Sample Output

```
🧠 Budget: ₹70,000
🎯 Purpose: Video Editing

🔧 Recommended Build:
- CPU: AMD Ryzen 5 5600
- GPU: NVIDIA RTX 3060
- RAM: 16GB DDR4
- Storage: 1TB NVMe SSD
- Motherboard: B550M
- PSU: 650W Bronze
```

## 📁 Installation

```bash
git clone https://github.com/your-username/pc-spec-recommender.git
cd pc-spec-recommender

# Create virtual environment
python -m venv venv
source venv/bin/activate   # For Linux/macOS
venv\Scripts\activate      # For Windows

# Install required packages
pip install -r requirements.txt

# Set up MongoDB URI
echo "MONGO_URI=your_mongodb_connection_string" > .env

# Run the Flask app
python app.py
```
