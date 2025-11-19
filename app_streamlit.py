"""
Interface Streamlit pour l'agent de debugging automatique.
Détecte automatiquement l'environnement du projet et permet de débugger des scripts Python.
"""
import streamlit as st
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from agent.main import DebugAgent
from agent.env_detector import EnvironmentDetector

load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Debug Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 1.75rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        font-size: 0.875rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }
    .stButton button {
        font-size: 0.875rem;
    }
    h1, h2, h3 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    .stSelectbox label, .stTextInput label {
        font-size: 0.875rem;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.875rem;
        padding: 0.5rem 1rem;
    }
    .success-box {
        background: #ecfdf5;
        border-left: 3px solid #10b981;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 0.75rem 0;
        font-size: 0.875rem;
    }
    .error-box {
        background: #fef2f2;
        border-left: 3px solid #ef4444;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 0.75rem 0;
        font-size: 0.875rem;
    }
    .info-box {
        background: #eff6ff;
        border-left: 3px solid #3b82f6;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 0.75rem 0;
        font-size: 0.875rem;
    }
    .metric-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 0.375rem;
        padding: 0.75rem;
        font-size: 0.875rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialiser le state
if 'env_detected' not in st.session_state:
    st.session_state.env_detected = False
if 'env_info' not in st.session_state:
    st.session_state.env_info = None
if 'debug_result' not in st.session_state:
    st.session_state.debug_result = None

st.markdown('<div class="main-header">Automatic Debug Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-powered Python debugging with automatic environment detection</div>', unsafe_allow_html=True)

# Sidebar pour la détection d'environnement
with st.sidebar:
    st.subheader("Project Environment")
    
    project_path = st.text_input(
        "Project Path",
        value=str(Path.cwd()),
        help="Path to your Python project"
    )
    
    if st.button("Detect Environment", type="primary", use_container_width=True):
        with st.spinner("Detecting..."):
            try:
                detector = EnvironmentDetector(Path(project_path))
                env_info = detector.detect_all()
                st.session_state.env_info = env_info
                st.session_state.env_detected = True
                st.success("Environment detected")
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.divider()
    
    # Afficher les informations d'environnement si détectées
    if st.session_state.env_detected and st.session_state.env_info:
        env = st.session_state.env_info
        
        st.markdown("**Python**")
        if env["python_version"]["found"]:
            st.caption(f"v{env['python_version']['version']}")
        
        st.markdown("**Virtual Environment**")
        if env["virtual_env"]["found"]:
            venvs = env["virtual_env"]["venvs"]
            conda = env["virtual_env"]["conda_envs"]
            
            if venvs:
                for venv in venvs:
                    st.caption(f"✓ {venv['name']} ({venv['type']})")
            if conda:
                for c in conda:
                    st.caption(f"✓ {c['name']} (conda)")
        else:
            st.caption("Not detected")
        
        st.markdown("**Dependencies**")
        if env["requirements"]["found"]:
            count = env["requirements"].get("count", 0)
            st.caption(f"{count} packages in requirements.txt")
        else:
            st.caption("No requirements.txt")
        
        st.markdown("**Python Files**")
        file_count = len(env["python_files"])
        st.caption(f"{file_count} files found")

# Main content
if not st.session_state.env_detected:
    st.info("Start by detecting your project environment in the sidebar")
    
    st.markdown("### How it works")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Detect**")
        st.caption("Automatically finds your Python environment, virtual environments, and project files")
    
    with col2:
        st.markdown("**Execute**")
        st.caption("Runs your script and captures errors with full traceback")
    
    with col3:
        st.markdown("**Fix**")
        st.caption("AI analyzes errors and proposes precise code corrections")

else:
    # Tabs pour les différentes fonctionnalités
    tab1, tab2, tab3 = st.tabs(["Debug Script", "Environment Details", "Settings"])
    
    with tab1:
        st.subheader("Debug Your Script")
        
        env = st.session_state.env_info
        python_files = env.get("python_files", [])
        
        if not python_files:
            st.warning("No Python files found in the project")
        else:
            # Sélectionner un fichier
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_file = st.selectbox(
                    "Select a Python file to debug",
                    options=python_files,
                    help="Choose a Python script from your project"
                )
            
            with col2:
                st.write("")
                st.write("")
                debug_button = st.button("Debug", type="primary", use_container_width=True)
            
            if debug_button and selected_file:
                script_path = Path(project_path) / selected_file
                
                groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", None) or st.session_state.get("groq_api_key")
                
                if not groq_api_key:
                    st.error("GROQ_API_KEY not found. Please add it in .env file or Settings tab.")
                else:
                    with st.spinner(f"Debugging {selected_file}..."):
                        try:
                            agent = DebugAgent(groq_api_key=groq_api_key)
                            result = agent.debug(str(script_path))
                            st.session_state.debug_result = result
                        except Exception as e:
                            st.error(f"Error during debugging: {e}")
            
            # Afficher les résultats
            if st.session_state.debug_result:
                result = st.session_state.debug_result
                
                if result["success"]:
                    if not result.get("needs_fixing"):
                        st.markdown('<div class="success-box"><b>Success:</b> Script executed without errors</div>', unsafe_allow_html=True)
                        
                        if result["execution"].get("stdout"):
                            st.markdown("**Output**")
                            st.code(result["execution"]["stdout"], language="text")
                    else:
                        st.markdown('<div class="error-box"><b>Error detected in script</b></div>', unsafe_allow_html=True)
                        
                        # Afficher l'erreur
                        with st.expander("Error Details", expanded=True):
                            st.code(result["execution"]["stderr"], language="text")
                        
                        # Analyse de l'IA
                        analysis = result["analysis"]
                        
                        st.markdown("**AI Analysis**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption(f"Error Type: `{analysis['error_type']}`")
                        with col2:
                            st.caption(f"Can Fix: {'Yes' if analysis['is_code_bug'] else 'No'}")
                        
                        st.markdown("**Analysis:**")
                        st.info(analysis["analysis"])
                        
                        if analysis["is_code_bug"]:
                            # Corrections proposées
                            st.markdown("**Proposed Corrections**")
                            
                            if analysis.get("lines_to_delete"):
                                st.markdown("*Lines to Delete:*")
                                for item in analysis["lines_to_delete"]:
                                    st.markdown(f"- Line **{item['line_number']}**: `{item['content']}`")
                                    st.caption(f"  {item['explanation']}")
                            
                            if analysis.get("lines_to_add"):
                                st.markdown("*Lines to Add:*")
                                for item in analysis["lines_to_add"]:
                                    st.markdown(f"- Line **{item['line_number']}**: `{item['content']}`")
                                    st.caption(f"  {item['explanation']}")
                            
                            # Bouton pour appliquer les corrections
                            st.divider()
                            col1, col2, col3 = st.columns([1, 1, 2])
                            
                            with col1:
                                if st.button("Apply Fixes", type="primary", use_container_width=True):
                                    with st.spinner("Applying corrections..."):
                                        try:
                                            fix_result = agent.apply_fixes(result)
                                            
                                            if fix_result["success"]:
                                                st.success(f"Applied {fix_result['applied_count']} corrections")
                                                
                                                # Ré-exécuter
                                                st.info("Re-running script to verify...")
                                                verification = agent.executor.execute(result["script_path"])
                                                
                                                if verification["success"]:
                                                    st.success("Script now runs successfully")
                                                    if verification["stdout"]:
                                                        st.code(verification["stdout"], language="text")
                                                else:
                                                    st.warning("Script still has errors:")
                                                    st.code(verification["stderr"], language="text")
                                            else:
                                                st.error(f"Failed to apply corrections: {fix_result['message']}")
                                        except Exception as e:
                                            st.error(f"Error applying fixes: {e}")
                            
                            with col2:
                                if st.button("Debug Again", use_container_width=True):
                                    st.session_state.debug_result = None
                                    st.rerun()
                        else:
                            st.warning(analysis.get("not_related_to_code", "Issue not related to code"))
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
    
    with tab2:
        st.subheader("Environment Details")
        
        if st.session_state.env_info:
            env = st.session_state.env_info
            
            # Python Info
            st.markdown("**Python Information**")
            py_info = env["python_version"]
            if py_info["found"]:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Version", py_info["version"])
                with col2:
                    st.caption(f"Executable: {py_info['executable']}")
            
            st.divider()
            
            # Virtual Environments
            st.markdown("**Virtual Environments**")
            venv_info = env["virtual_env"]
            if venv_info["found"]:
                for venv in venv_info.get("venvs", []):
                    with st.expander(f"{venv['name']} ({venv['type']})"):
                        st.caption(f"**Path:** `{venv['path']}`")
                        st.caption(f"**Python:** `{venv['python_executable']}`")
                
                for conda in venv_info.get("conda_envs", []):
                    st.caption(f"{conda['name']} (conda) {'[Active]' if conda.get('active') else ''}")
            else:
                st.caption("No virtual environments detected")
            
            st.divider()
            
            # Package Manager
            st.markdown("**Package Managers**")
            pkg_info = env["package_manager"]
            if pkg_info["found"]:
                st.caption("Detected: " + ", ".join(pkg_info["managers"]))
                
                for file, exists in pkg_info["files"].items():
                    if exists:
                        st.caption(f"✓ {file}")
            else:
                st.caption("No package manager files detected")
            
            st.divider()
            
            # Requirements
            st.markdown("**Dependencies**")
            req_info = env["requirements"]
            if req_info["found"]:
                st.caption(f"Found {req_info.get('count', 0)} packages in requirements.txt")
                
                with st.expander("View all packages"):
                    for pkg in req_info.get("packages", []):
                        st.code(pkg, language="text")
            else:
                st.caption("No requirements.txt found")
            
            st.divider()
            
            # Python Files
            st.markdown("**Python Files**")
            files = env.get("python_files", [])
            st.caption(f"Found {len(files)} Python files")
            
            if files:
                with st.expander("View all files"):
                    for file in files:
                        st.caption(f"- {file}")
    
    with tab3:
        st.subheader("Settings")
        
        st.markdown("**API Configuration**")
        
        env_key = os.getenv("GROQ_API_KEY")
        if env_key:
            st.success("GROQ_API_KEY loaded from .env file")
            st.caption("Your API key is configured correctly")
        else:
            current_key = st.session_state.get("groq_api_key", "")
            
            groq_key = st.text_input(
                "Groq API Key",
                value=current_key,
                type="password",
                help="Your Groq API key for AI analysis"
            )
            
            if st.button("Save API Key"):
                st.session_state.groq_api_key = groq_key
                st.success("API key saved")
        
        st.divider()
        
        st.markdown("**About**")
        st.caption("Automatic Debug Agent v1.0")
        st.caption("Powered by Groq AI (Llama 3.3 70B)")
        st.caption("Built with Streamlit")

# Footer
st.divider()
st.caption("Tip: Set GROQ_API_KEY in your .env file or in Settings")
