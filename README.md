# Transportation Optimization with MILP

A Python-based optimization system that uses Mixed-Integer Linear Programming (MILP) to solve complex transportation and logistics problems. This application helps in finding the most cost-effective and time-efficient ways to distribute goods across multiple locations while considering various constraints.

## Features

- **Multi-objective Optimization**: Optimize for both cost and delivery time
- **Flexible Input**: Handle multiple warehouses, plants, and transportation modes
- **Interactive Web Interface**: User-friendly Streamlit-based interface
- **Data-Driven**: Process real-world transportation data in CSV format
- **Constraint Management**: Handle various constraints including:
  - Warehouse and plant capacities
  - Vehicle availability
  - Maximum delivery time
  - Transportation mode capacities

## Prerequisites

- Python 3.7+
- pip (Python package manager)

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- Git (for version control)
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   # Using HTTPS
   git clone https://github.com/Data-Science-PIHC/Transportation-Optimization-MILP.git
   
   # Or using SSH (if you have SSH keys set up)
   # git clone git@github.com:Data-Science-PIHC/Transportation-Optimization-MILP.git
   
   # Navigate to project directory
   cd Transportation-Optimization-MILP
   ```

2. **Set up the development environment**
   ```bash
   # Method 1: Using the setup script (recommended)
   python init_project.py
   
   # Method 2: Manual setup
   # 1. Create and activate virtual environment
   #    Windows: python -m venv venv && .\venv\Scripts\activate
   #    Unix/Mac: python -m venv venv && source venv/bin/activate
   # 2. Install dependencies
   #    pip install -r requirements_optimizer.txt
   ```

3. **Run the application**
   ```bash
   # Activate virtual environment if not already activated
   # Windows: .\venv\Scripts\activate
   # Unix/Mac: source venv/bin/activate
   
   # Run the Streamlit app
   streamlit run distribution_optimizer.py
   ```

   The application should open in your default web browser at `http://localhost:8501`

## Project Structure

```
Transportation Optimization - MILP/
├── dataset/                   # Data files
│   ├── wh_capacity.csv       # Warehouse capacities
│   ├── pl_capacity.csv       # Plant capacities
│   ├── tp_capacity.csv       # Transport mode capacities
│   └── tp_route.csv          # Transportation routes
├── distribution_optimizer.py  # Main application code
└── requirements_optimizer.txt # Project dependencies
```

## Data Format

### Input Files

1. **Warehouse Capacities (wh_capacity.csv)**
   - `warehouse_name`: Unique identifier for each warehouse (e.g., WH01, WH02)
   - `capacity`: Maximum storage capacity of the warehouse
   - `stock_level`: Current inventory level in the warehouse

2. **Plant Capacities (pl_capacity.csv)**
   - `plant_name`: Unique identifier for each plant (e.g., PlantA)
   - `capacity`: Production capacity of the plant
   - `stock_level`: Current inventory level at the plant

3. **Transport Modes (tp_capacity.csv)**
   - `mode_name`: Name of the transport mode (e.g., Ship, Small Truck, Big Truck)
   - `weight_capacity`: Maximum weight capacity per vehicle/unit

4. **Transport Routes (tp_route.csv)**
   - `origin`: Origin location (Plant or Warehouse ID)
   - `destination`: Destination location (Warehouse ID)
   - `mode_name`: Transport mode to be used for this route
   - `lead_time (days)`: Estimated delivery time in days
   - `total_cost`: Total cost for using this route

## Usage

1. Prepare your input data files in the `dataset` directory following the required formats.

2. Run the Streamlit application:
   ```bash
   streamlit run distribution_optimizer.py
   ```

3. Use the web interface to:
   - Input total demand
   - Set maximum delivery time constraints
   - Select available warehouses
   - Configure vehicle limits per warehouse and transport mode

4. View the optimization results including:
   - Optimal shipment quantities
   - Total cost breakdown
   - Delivery time estimates
   - Resource utilization

## Optimization Models

The system implements two main optimization models:

1. **Cost Optimization**: Minimizes total transportation and operational costs
2. **Time Optimization**: Minimizes total delivery time while respecting cost constraints

## Dependencies

- Python 3.7+
- pandas >= 1.3.0
- pulp >= 2.7.0
- streamlit >= 1.31.0
- seaborn >= 0.11.0
- matplotlib >= 3.3.0
- numpy >= 1.19.0
- openpyxl >= 3.0.0 (for Excel file support)

## 🤝 Contributing

We welcome contributions! Please follow these steps to contribute:

1. **Fork** the repository
2. **Clone** your forked repository
   ```bash
   git clone https://github.com/your-username/Transportation-Optimization-MILP.git
   ```
3. **Create a new branch** for your feature or bugfix
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-description
   ```
4. **Make your changes** and test them
5. **Commit** your changes with a descriptive message
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```
6. **Push** to your forked repository
   ```bash
   git push origin your-branch-name
   ```
7. Create a **Pull Request** to the `main` branch of the original repository

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally
- Consider starting the commit message with an applicable emoji:
  - ✨ `:sparkles:` When adding a new feature
  - 🐛 `:bug:` When fixing a bug
  - 📚 `:books:` When updating documentation
  - ♻️ `:recycle:` When refactoring code
  - 🚧 `:construction:` When work is in progress

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ✨ Contributors

<a href="https://github.com/Data-Science-PIHC/Transportation-Optimization-MILP/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Data-Science-PIHC/Transportation-Optimization-MILP" />
</a>

## 🙏 Acknowledgments

- PuLP for mathematical optimization
- Streamlit for the web interface
- Pandas for data manipulation
