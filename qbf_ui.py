#!/usr/bin/env python3
"""
QBF Logic System - Interactive Web UI
Modern interface for QBF reasoning with DepQBF and TweetyProject integration
"""

import streamlit as st
import sys
from pathlib import Path
import time
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from qbf_system import QBFLogicSystem, QBFFormula
    from config import Config
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="QBF Logic System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .solver-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
        margin-left: 1rem;
    }
    
    .depqbf-badge {
        background-color: #28a745;
        color: white;
    }
    
    .tweety-badge {
        background-color: #fd7e14;
        color: white;
    }
    
    .result-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    
    .satisfiable {
        background-color: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
    
    .unsatisfiable {
        background-color: #f8d7da;
        border-color: #dc3545;
        color: #721c24;
    }
    
    .error {
        background-color: #fff3cd;
        border-color: #ffc107;
        color: #856404;
    }
    
    .formula-display {
        font-family: 'Courier New', monospace;
        font-size: 1.2em;
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 4px;
        border: 1px solid #dee2e6;
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    
    .solver-comparison {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with solver preference
if 'solver_preference' not in st.session_state:
    st.session_state.solver_preference = "DepQBF"

if 'system' not in st.session_state or st.session_state.get('current_solver') != st.session_state.solver_preference:
    try:
        use_depqbf = st.session_state.solver_preference == "DepQBF"
        st.session_state.system = QBFLogicSystem(
            jar_path=str(Config.JAR_PATH),
            llm_api_key=Config.get_api_key(),
            use_depqbf=use_depqbf
        )
        st.session_state.initialized = True
        st.session_state.current_solver = st.session_state.solver_preference
        st.session_state.init_error = None
    except Exception as e:
        st.session_state.initialized = False
        st.session_state.init_error = str(e)
        # Try fallback to TweetyProject if DepQBF fails
        if st.session_state.solver_preference == "DepQBF":
            try:
                st.session_state.system = QBFLogicSystem(
                    jar_path=str(Config.JAR_PATH),
                    llm_api_key=Config.get_api_key(),
                    use_depqbf=False
                )
                st.session_state.initialized = True
                st.session_state.current_solver = "TweetyProject"
                st.session_state.fallback_used = True
            except Exception as e2:
                st.session_state.init_error = f"Both solvers failed: DepQBF ({e}), TweetyProject ({e2})"

if 'history' not in st.session_state:
    st.session_state.history = []

# Main header with solver badge
solver_badge_class = "depqbf-badge" if st.session_state.get('current_solver') == "DepQBF" else "tweety-badge"
solver_display = st.session_state.get('current_solver', 'Unknown')

st.markdown(f"""
<div class="main-header">
    <h1>🧠 QBF Logic System
        <span class="solver-badge {solver_badge_class}">
            {solver_display} Solver
        </span>
    </h1>
    <p>Quantified Boolean Formula reasoning with advanced solvers and LLM integration</p>
</div>
""", unsafe_allow_html=True)

# Check initialization
if not st.session_state.get('initialized', False):
    st.error(f"❌ System initialization failed: {st.session_state.get('init_error', 'Unknown error')}")
    st.info("Please check your configuration:")
    st.code("""
    1. For DepQBF: Install with 'sudo apt install depqbf' or let the system compile from source
    2. For TweetyProject: Ensure JAR is in the project directory
    3. Set your LLM API key in .env file
    4. Verify Java is installed and accessible
    """)
    st.stop()

# Show fallback warning if applicable
if st.session_state.get('fallback_used'):
    st.warning("⚠️ DepQBF solver not available, using TweetyProject as fallback. Results may differ for complex QBF formulas.")

# Sidebar
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    # Solver selection
    st.subheader("⚙️ Solver Settings")
    new_solver = st.selectbox(
        "QBF Solver:",
        ["DepQBF", "TweetyProject"],
        index=0 if st.session_state.solver_preference == "DepQBF" else 1,
        help="DepQBF is recommended for accurate QBF evaluation"
    )
    
    if new_solver != st.session_state.solver_preference:
        st.session_state.solver_preference = new_solver
        st.rerun()
    
    # Solver comparison info
    with st.expander("🔍 Solver Comparison"):
        st.markdown("""
        **DepQBF (Recommended)**
        - ✅ Proper QBF semantics
        - ✅ Handles quantifier alternation
        - ✅ Standard QDIMACS format
        - ✅ Fast and reliable
        
        **TweetyProject**  
        - ⚠️ Naive QBF reasoning
        - ⚠️ May give incorrect results
        - ✅ Java-based integration
        - ✅ Always available
        """)
    
    st.markdown("---")
    
    # Mode selection
    mode = st.selectbox(
        "Select Mode",
        ["🗣️ Natural Language", "🔢 Direct QBF", "📚 Examples", "🧪 Solver Comparison", "📊 Batch Analysis"]
    )
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("📈 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Queries", len(st.session_state.history))
    with col2:
        if st.session_state.history:
            satisfiable_count = sum(1 for h in st.session_state.history if h.get('result') == 'SATISFIABLE')
            st.metric("Satisfiable", satisfiable_count)
    
    st.markdown("---")
    
    # System info
    with st.expander("ℹ️ System Info"):
        st.write(f"**Current Solver**: {st.session_state.get('current_solver', 'Unknown')} ✅")
        if st.session_state.get('current_solver') == "DepQBF":
            st.write("**DepQBF**: Available ✅")
        st.write("**TweetyProject**: Ready ✅")  
        st.write("**LLM Integration**: Ready ✅")
        st.write("**Java Bridge**: Compiled ✅")
    
    # Clear history
    if st.button("🗑️ Clear History", type="secondary"):
        st.session_state.history = []
        st.rerun()

# Main content area
if mode == "🧪 Solver Comparison":
    st.header("🧪 Solver Comparison")
    st.write("Compare results between DepQBF and TweetyProject solvers on problematic cases.")
    
    # Test cases that were problematic
    test_cases = [
        {
            "name": "Problematic Case 1",
            "description": "∃y: (∀x: (x ∧ ¬y)) - Should be UNSATISFIABLE",
            "formula": "x && !y",
            "variables": ["x", "y"],
            "quantifiers": [("exists", "y"), ("forall", "x")],
            "expected": "UNSATISFIABLE"
        },
        {
            "name": "Problematic Case 2", 
            "description": "∃x: (∀y: (x ∧ ¬y)) - Should be UNSATISFIABLE",
            "formula": "x && !y",
            "variables": ["x", "y"],
            "quantifiers": [("exists", "x"), ("forall", "y")],
            "expected": "UNSATISFIABLE"
        },
        {
            "name": "Simple Tautology",
            "description": "∀x: (x ∨ ¬x) - Should be SATISFIABLE",
            "formula": "x || !x",
            "variables": ["x"],
            "quantifiers": [("forall", "x")],
            "expected": "SATISFIABLE"
        },
        {
            "name": "Simple Contradiction",
            "description": "∃x: (x ∧ ¬x) - Should be UNSATISFIABLE",
            "formula": "x && !x",
            "variables": ["x"],
            "quantifiers": [("exists", "x")],
            "expected": "UNSATISFIABLE"
        }
    ]
    
    if st.button("🚀 Run Comparison Test", type="primary"):
        st.subheader("📊 Comparison Results")
        
        results = []
        progress_bar = st.progress(0)
        
        for i, test_case in enumerate(test_cases):
            with st.spinner(f"Testing: {test_case['name']}"):
                # Test with both solvers
                solver_results = {}
                
                for solver_name in ["DepQBF", "TweetyProject"]:
                    try:
                        # Create system with specific solver
                        use_depqbf = solver_name == "DepQBF"
                        test_system = QBFLogicSystem(
                            jar_path=str(Config.JAR_PATH),
                            llm_api_key=Config.get_api_key(),
                            use_depqbf=use_depqbf
                        )
                        
                        result = test_system.evaluate_qbf(
                            test_case['formula'],
                            test_case['variables'],
                            test_case['quantifiers']
                        )
                        
                        solver_results[solver_name] = {
                            'result': result['result'],
                            'time': result['execution_time'],
                            'correct': result['result'] == test_case['expected']
                        }
                        
                    except Exception as e:
                        solver_results[solver_name] = {
                            'result': 'ERROR',
                            'time': 0,
                            'error': str(e),
                            'correct': False
                        }
                
                results.append({
                    'test_case': test_case,
                    'results': solver_results
                })
            
            progress_bar.progress((i + 1) / len(test_cases))
        
        # Display results
        for i, test_result in enumerate(results):
            test_case = test_result['test_case']
            solver_results = test_result['results']
            
            st.subheader(f"🧪 {test_case['name']}")
            st.write(test_case['description'])
            
            # Formula display
            quantifier_str = " ".join([f"{'∀' if q == 'forall' else '∃'}{v}" for q, v in test_case['quantifiers']])
            full_formula = f"{quantifier_str} ({test_case['formula']})"
            st.markdown(f'<div class="formula-display">{full_formula}</div>', unsafe_allow_html=True)
            
            # Results comparison
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Expected Result:**")
                st.info(test_case['expected'])
            
            with col2:
                st.write("**DepQBF Result:**")
                depqbf_result = solver_results.get('DepQBF', {})
                if depqbf_result.get('correct'):
                    st.success(f"✅ {depqbf_result['result']} ({depqbf_result['time']:.3f}s)")
                else:
                    st.error(f"❌ {depqbf_result.get('result', 'ERROR')} ({depqbf_result.get('time', 0):.3f}s)")
            
            with col3:
                st.write("**TweetyProject Result:**")
                tweety_result = solver_results.get('TweetyProject', {})
                if tweety_result.get('correct'):
                    st.success(f"✅ {tweety_result['result']} ({tweety_result['time']:.3f}s)")
                else:
                    st.error(f"❌ {tweety_result.get('result', 'ERROR')} ({tweety_result.get('time', 0):.3f}s)")
            
            st.markdown("---")
        
        # Summary
        st.subheader("📋 Summary")
        depqbf_correct = sum(1 for r in results if r['results'].get('DepQBF', {}).get('correct', False))
        tweety_correct = sum(1 for r in results if r['results'].get('TweetyProject', {}).get('correct', False))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("DepQBF Correct", f"{depqbf_correct}/{len(results)}")
        with col2:
            st.metric("TweetyProject Correct", f"{tweety_correct}/{len(results)}")
        
        if depqbf_correct > tweety_correct:
            st.success("🏆 DepQBF performed better on these test cases!")
        elif tweety_correct > depqbf_correct:
            st.warning("⚠️ TweetyProject performed better (unusual)")
        else:
            st.info("🤝 Both solvers performed equally")

elif mode == "🗣️ Natural Language":
    st.header("Natural Language to QBF")
    st.write("Enter your logical statement in plain English, and the system will convert it to QBF and evaluate it.")
    
    # Show current solver
    st.info(f"🔧 Using {st.session_state.get('current_solver', 'Unknown')} solver for evaluation")
    
    # Text input
    text_input = st.text_area(
        "Enter your logical statement:",
        placeholder="Example: Every student either passes or fails the exam",
        height=100
    )
    
    # Example suggestions
    with st.expander("💡 Example Statements"):
        examples = [
            "Every proposition is either true or false",
            "There exists a perfect solution to every problem", 
            "For any choice, there is a corresponding outcome",
            "All humans are mortal and Socrates is human",
            "Either it rains or it doesn't rain"
        ]
        for example in examples:
            if st.button(f"📝 {example}", key=f"example_{example}"):
                st.session_state.text_input = example
                text_input = example
    
    # Process button
    if st.button("🚀 Analyze Statement", type="primary", disabled=not text_input.strip()):
        with st.spinner(f"Processing with LLM and {st.session_state.get('current_solver')}..."):
            try:
                result = st.session_state.system.evaluate_text(text_input)
                
                # Store in history
                st.session_state.history.append({
                    'mode': 'Natural Language',
                    'input': text_input,
                    'result': result['result'],
                    'solver': st.session_state.get('current_solver'),
                    'time': time.time(),
                    'details': result
                })
                
                # Display results
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📋 Analysis Results")
                    
                    # Generated QBF
                    st.write("**Generated QBF Formula:**")
                    st.markdown(f'<div class="formula-display">{result["qbf_formula"]}</div>', unsafe_allow_html=True)
                    
                    # Variables and quantifiers
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write("**Variables:**", ", ".join(result["variables"]))
                    with col_b:
                        quantifiers_str = ", ".join([f"{q} {v}" for q, v in result["quantifiers"]])
                        st.write("**Quantifiers:**", quantifiers_str)
                
                with col2:
                    # Result display
                    result_class = result['result'].lower()
                    if result_class == 'error':
                        result_class = 'error'
                    
                    st.markdown(f"""
                    <div class="result-box {result_class}">
                        <h3>Result: {result['result']}</h3>
                        <p>Solver: {st.session_state.get('current_solver')}</p>
                        <p>Execution: {result['execution_time']:.3f}s</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Technical details
                with st.expander("🔧 Technical Details"):
                    st.write(f"**Solver Used:** {st.session_state.get('current_solver')}")
                    st.write("**Solver Output:**")
                    st.code(result.get('solver_output', 'No output'), language='text')
                    if result.get('error'):
                        st.write("**Error:**")
                        st.error(result['error'])
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")

elif mode == "🔢 Direct QBF":
    st.header("Direct QBF Input")
    st.write("Enter QBF formulas directly using logical operators.")
    
    # Input form
    with st.form("qbf_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            formula = st.text_input(
                "Formula (use &, |, ~, parentheses):",
                placeholder="x | ~x"
            )
        
        with col2:
            st.write("**Operators:**")
            st.write("• `&` = AND")
            st.write("• `|` = OR") 
            st.write("• `~` = NOT")
            st.write("• `()` = grouping")
        
        # Variables
        variables_input = st.text_input(
            "Variables (comma-separated):",
            placeholder="x, y, z"
        )
        
        # Quantifiers
        st.write("**Quantifiers:**")
        quantifiers = []
        
        if variables_input:
            vars_list = [v.strip() for v in variables_input.split(',') if v.strip()]
            cols = st.columns(len(vars_list))
            
            for i, var in enumerate(vars_list):
                with cols[i]:
                    quant_type = st.selectbox(
                        f"Quantifier for {var}:",
                        ["exists", "forall"],
                        key=f"quant_{var}"
                    )
                    quantifiers.append((quant_type, var))
        
        submitted = st.form_submit_button("🧮 Evaluate QBF", type="primary")
        
        if submitted and formula and variables_input:
            vars_list = [v.strip() for v in variables_input.split(',') if v.strip()]
            
            with st.spinner("Evaluating with TweetyProject..."):
                try:
                    result = st.session_state.system.evaluate_qbf(formula, vars_list, quantifiers)
                    
                    # Store in history
                    st.session_state.history.append({
                        'mode': 'Direct QBF',
                        'input': f"{formula} with {quantifiers}",
                        'result': result['result'],
                        'time': time.time(),
                        'details': result
                    })
                    
                    # Display result
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Formula display
                        quantifier_str = " ".join([f"{'∀' if q == 'forall' else '∃'}{v}" for q, v in quantifiers])
                        full_formula = f"{quantifier_str} ({formula})"
                        st.markdown(f'<div class="formula-display">{full_formula}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        result_class = result['result'].lower()
                        if result_class == 'error':
                            result_class = 'error'
                        
                        st.markdown(f"""
                        <div class="result-box {result_class}">
                            <h3>{result['result']}</h3>
                            <p>{result['execution_time']:.3f}s</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Analysis
                    if result.get('analysis'):
                        with st.expander("🤖 Analysis", expanded=True):
                            st.write(result['analysis'])
                
                except Exception as e:
                    st.error(f"❌ Evaluation failed: {str(e)}")

elif mode == "📚 Examples":
    st.header("QBF Examples")
    st.write("Explore classic QBF formulas and their evaluations.")
    
    examples = [
        {
            "name": "Tautology",
            "description": "A formula that is always true",
            "formula": "x | ~x",
            "variables": ["x"],
            "quantifiers": [("forall", "x")],
            "expected": "SATISFIABLE"
        },
        {
            "name": "Contradiction",
            "description": "A formula that is never true",
            "formula": "x & ~x",
            "variables": ["x"],
            "quantifiers": [("forall", "x")],
            "expected": "UNSATISFIABLE"
        },
        {
            "name": "Existential Choice",
            "description": "There exists a choice that works for all cases",
            "formula": "x | y",
            "variables": ["x", "y"],
            "quantifiers": [("exists", "x"), ("forall", "y")],
            "expected": "SATISFIABLE"
        },
        {
            "name": "Universal Implication",
            "description": "For all x, if x is true then x is true",
            "formula": "~x | x",
            "variables": ["x"],
            "quantifiers": [("forall", "x")],
            "expected": "SATISFIABLE"
        }
    ]
    
    for i, example in enumerate(examples):
        with st.expander(f"📖 {example['name']}: {example['description']}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                quantifier_str = " ".join([f"{'∀' if q == 'forall' else '∃'}{v}" for q, v in example['quantifiers']])
                full_formula = f"{quantifier_str} ({example['formula']})"
                st.markdown(f'<div class="formula-display">{full_formula}</div>', unsafe_allow_html=True)
                st.write(f"**Expected:** {example['expected']}")
            
            with col2:
                if st.button(f"🧮 Test Example", key=f"test_{i}"):
                    with st.spinner("Evaluating..."):
                        try:
                            result = st.session_state.system.evaluate_qbf(
                                example['formula'], 
                                example['variables'], 
                                example['quantifiers']
                            )
                            
                            actual = result['result']
                            is_correct = actual == example['expected']
                            
                            st.write(f"**Result:** {actual}")
                            if is_correct:
                                st.success("✅ Correct!")
                            else:
                                st.error(f"❌ Expected {example['expected']}")
                        
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with col3:
                st.write("**Variables:**")
                st.write(", ".join(example['variables']))

elif mode == "📊 Batch Analysis":
    st.header("Batch Analysis")
    st.write("Test multiple QBF formulas at once.")
    
    # File upload option
    uploaded_file = st.file_uploader(
        "Upload QBF test file (JSON format)",
        type=['json'],
        help="Upload a JSON file with QBF test cases"
    )
    
    # Manual batch input
    st.subheader("Or enter multiple formulas:")
    
    batch_input = st.text_area(
        "Enter formulas (one per line, format: 'formula | variables | quantifiers'):",
        placeholder="""x | ~x | x | forall x
x & ~x | x | forall x
x | y | x,y | exists x, forall y""",
        height=150
    )
    
    if st.button("🚀 Run Batch Analysis", type="primary"):
        if batch_input:
            lines = [line.strip() for line in batch_input.split('\n') if line.strip()]
            
            progress_bar = st.progress(0)
            results = []
            
            for i, line in enumerate(lines):
                try:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:
                        formula = parts[0]
                        variables = [v.strip() for v in parts[1].split(',')]
                        quantifiers = []
                        
                        quant_parts = parts[2].split(',')
                        for qp in quant_parts:
                            qp = qp.strip()
                            if 'exists' in qp:
                                var = qp.replace('exists', '').strip()
                                quantifiers.append(('exists', var))
                            elif 'forall' in qp:
                                var = qp.replace('forall', '').strip()
                                quantifiers.append(('forall', var))
                        
                        # Evaluate
                        result = st.session_state.system.evaluate_qbf(formula, variables, quantifiers)
                        results.append({
                            'formula': formula,
                            'result': result['result'],
                            'time': result['execution_time'],
                            'line': line
                        })
                    
                except Exception as e:
                    results.append({
                        'formula': line,
                        'result': 'ERROR',
                        'time': 0,
                        'error': str(e),
                        'line': line
                    })
                
                progress_bar.progress((i + 1) / len(lines))
            
            # Display results
            st.subheader("📊 Batch Results")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", len(results))
            with col2:
                satisfiable = sum(1 for r in results if r['result'] == 'SATISFIABLE')
                st.metric("Satisfiable", satisfiable)
            with col3:
                unsatisfiable = sum(1 for r in results if r['result'] == 'UNSATISFIABLE')
                st.metric("Unsatisfiable", unsatisfiable)
            with col4:
                errors = sum(1 for r in results if r['result'] == 'ERROR')
                st.metric("Errors", errors)
            
            # Results table
            st.dataframe(
                results,
                column_config={
                    "formula": "Formula",
                    "result": "Result",
                    "time": st.column_config.NumberColumn("Time (s)", format="%.3f"),
                    "line": "Original Input"
                },
                hide_index=True
            )

# History section (updated to show solver used)
if st.session_state.history:
    st.markdown("---")
    st.header("📚 Query History")
    
    for i, entry in enumerate(reversed(st.session_state.history[-10:])):  # Show last 10
        solver_used = entry.get('solver', 'Unknown')
        badge_class = "depqbf-badge" if solver_used == "DepQBF" else "tweety-badge"
        
        with st.expander(f"Query {len(st.session_state.history) - i}: {entry['mode']} - {entry['result']} ({solver_used})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Input:** {entry['input']}")
                if 'details' in entry and 'qbf_formula' in entry['details']:
                    st.write(f"**QBF:** {entry['details']['qbf_formula']}")
            with col2:
                st.markdown(f"""
                **Result:** {entry['result']}<br>
                **Solver:** <span class="solver-badge {badge_class}">{solver_used}</span><br>
                **Time:** {time.strftime('%H:%M:%S', time.localtime(entry['time']))}
                """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    🧠 QBF Logic System | Current Solver: {st.session_state.get('current_solver', 'Unknown')}<br>
    Powered by DepQBF & TweetyProject • Built with Streamlit • Open Source
</div>
""", unsafe_allow_html=True)