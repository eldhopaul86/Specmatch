💻 AI-Powered PC Spec Recommender - SPECMATCH
An AI-based PC specification recommendation system that suggests optimal PC builds based on your budget and purpose (e.g., gaming, editing, office work). This tool helps users make smarter hardware choices using machine learning and optimization techniques.

🚀 Features
🔢 Smart Recommendations: Suggests CPU, GPU, RAM, Storage, etc., tailored to budget and use-case.

🧠 AI & ML Models: Predicts components using trained regression/classification models.

🧬 Optimization Engine: Uses Genetic Algorithm/Random Forest to find the best combination.

🌐 User-Friendly Interface: Simple web interface using Flask (Python) and HTML/CSS frontend.

📸 Demo
Add a screenshot or link to a demo video here (e.g., hosted on Vercel/Render)


🛠️ Tech Stack
Frontend: HTML, CSS, Javascript ,Tailwind CSS

Backend: Flask (Python)

Database: MongoDB

Machine Learning: Scikit-learn, PyTorch

Optimization:  Random Forest

📥 How It Works
User Input:

Enters budget and purpose (e.g., ₹50,000 for gaming)

Model Processing:

Predicts best PC configuration using ML models

Optimizes components using budget constraints

Output:

Displays recommended CPU, GPU, RAM, Storage, etc.

📦 Installation
bash
Copy
Edit
git clone https://github.com/your-username/pc-spec-recommender.git
cd pc-spec-recommender
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
Note: Make sure to set your MongoDB URI in .env file.

⚙️ Sample Output

🧠 Budget: ₹70,000
🎯 Purpose: Video Editing

🔧 Recommended Build:
- CPU: AMD Ryzen 5 5600
- GPU: NVIDIA RTX 3060
- RAM: 16GB DDR4
- Storage: 1TB NVMe SSD
- Motherboard: B550M
- PSU: 650W Bronze
