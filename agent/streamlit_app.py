"""
Interface Streamlit pour le débuggeur automatique.
Détermine automatiquement l'environnement et débugge vos scripts Python.
"""
import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from executor import execute_script, get_numbered_source
from ai_analyzer import AIAnalyzer
from file_patcher import FilePatcher
from env_detector import EnvironmentDetector

load_dotenv()

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
        margin-bottom: 0.25rem;
    }
    .subtitle {
        font-size: 0.875rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }
    .success-box {
        background: #ecfdf5;
        border-left: 3px solid #10b981;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 0.75rem 0;
    }
    .error-box {
        background: #fef2f2;
        border-left: 3px solid #ef4444;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 0.75rem 0;
    }
    .info-box {
        background: #eff6ff;
        border-left: 3px solid #3b82f6;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 0.75rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'env_detected' not in st.session_state:
    st.session_state.env_detected = False
if 'env_info' not in st.session_state:
    st.session_state.env_info = None
if 'debug_result' not in st.session_state:
    st.session_state.debug_result = None

# Header
st.markdown('<div class="main-header">Automatic Debug Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-powered Python debugging with environment detection</div>', unsafe_allow_html=True)

# Sidebar - Environment Detection
with st.sidebar:
    st.subheader("Project Environment")
    
    project_path = st.text_input(
        "Project Path",
        value=str(Path.cwd()),
        help="Path to your Python project"
    )
    
    if st.button("Detect Environment", type="primary", use_container_width=True):
        with st.spinner("Detecting environment..."):
            try:
                detector = EnvironmentDetector(Path(project_path))
                env_info = detector.detect_all()
                st.session_state.env_info = env_info
                st.session_state.env_detected = True
                st.success("Environment detected!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.divider()
    
    # Display environment info if detected
    if st.session_state.env_detected and st.session_state.env_info:
        env = st.session_state.env_info
        
        st.markdown("**Python Version**")
        if env["python_version"]["found"]:
            st.caption(f"v{env['python_version']['version']}")
        
        st.markdown("**Virtual Environments**")
        if env["virtual_env"]["found"]:
            for venv in env["virtual_env"]["venvs"]:
                st.caption(f"✓ {venv['name']} ({venv['type']})")
        else:
            st.caption("Not detected")
        
        st.markdown("**Dependencies**")
        if env["requirements"]["found"]:
            count = env["requirements"].get("count", 0)
            st.caption(f"{count} packages found")
        else:
            st.caption("No requirements.txt")
        
        st.markdown("**Python Files**")
        file_count = len(env["python_files"])
        st.caption(f"{file_count} files available")

# Main content
if not st.session_state.env_detected:
    st.info("Start by detecting your project environment in the sidebar")
    
    st.markdown("### How it works")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Detect**")
        st.caption("Finds your environment and project files")
    
    with col2:
        st.markdown("**Execute**")
        st.caption("Runs your script and captures errors")
    
    with col3:
        st.markdown("**Fix**")
        st.caption("AI analyzes and proposes corrections")

else:
    # Tabs for different features
    tab1, tab2, tab3 = st.tabs(["Debug Script", "Environment", "Settings"])
    
    with tab1:
        st.subheader("Debug Your Script")
        
        env = st.session_state.env_info
        python_files = env.get("python_files", [])
        
        if not python_files:
            st.warning("No Python files found in the project")
        else:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_file = st.selectbox(
                    "Select a Python file",
                    options=python_files,
                    help="Choose a script to debug"
                )
            
            with col2:
                st.write("")
                st.write("")
                debug_button = st.button("Debug", type="primary", use_container_width=True)
            
            if debug_button and selected_file:
                script_path = Path(project_path) / selected_file
                
                groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
                
                if not groq_api_key:
                    st.error("GROQ_API_KEY not found. Add it in .env or Settings.")
                else:
                    with st.spinner(f"Debugging {selected_file}..."):
                        try:
                            # Execute script
                            execution = execute_script(script_path)
                            
                            if execution["success"]:
                                st.markdown('<div class="success-box"><b>Success!</b> Script ran without errors</div>', unsafe_allow_html=True)
                                if execution["stdout"]:
                                    st.code(execution["stdout"], language="text")
                            else:
                                st.markdown('<div class="error-box"><b>Error detected</b></div>', unsafe_allow_html=True)
                                
                                with st.expander("Error Details", expanded=True):
                                    st.code(execution["stderr"], language="text")
                                
                                # Analyze with AI
                                analyzer = AIAnalyzer(groq_api_key)
                                numbered_code = get_numbered_source(script_path)
                                analysis = analyzer.analyze(numbered_code, execution["traceback"])
                                
                                # Display analysis
                                st.markdown("**AI Analysis**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.caption(f"Error Type: `{analysis['error_type']}`")
                                with col2:
                                    st.caption(f"Code Issue: {'Yes' if analysis['is_code_bug'] else 'No'}")
                                
                                st.info(analysis["analysis"])
                                
                                if analysis["is_code_bug"]:
                                    st.markdown("**Proposed Corrections**")
                                    
                                    if analysis.get("lines_to_delete"):
                                        st.markdown("*Lines to Remove:*")
                                        for item in analysis["lines_to_delete"]:
                                            st.markdown(f"- Line **{item['line_number']}**: `{item['content']}`")
                                    
                                    if analysis.get("lines_to_add"):
                                        st.markdown("*Lines to Add:*")
                                        for item in analysis["lines_to_add"]:
                                            st.markdown(f"- Line **{item['line_number']}**: `{item['content']}`")
                                    
                                    st.divider()
                                    
                                    if st.button("Apply Fixes", type="primary", use_container_width=True):
                                        with st.spinner("Applying corrections..."):
                                            try:
                                                patcher = FilePatcher()
                                                corrections = []
                                                
                                                for delete in analysis.get("lines_to_delete", []):
                                                    corrections.append({
                                                        "line_number": delete["line_number"],
                                                        "new_code": ""
                                                    })
                                                
                                                for add in analysis.get("lines_to_add", []):
                                                    corrections.append({
                                                        "line_number": add["line_number"],
                                                        "new_code": add["content"]
                                                    })
                                                
                                                fix_result = patcher.apply_corrections(script_path, corrections)
                                                
                                                if fix_result["success"]:
                                                    st.success(f"Applied {fix_result['applied_count']} correction(s)")
                                                    st.caption(f"Backup: {fix_result['backup_path']}")
                                                    
                                                    # Re-execute to verify
                                                    st.info("Re-running script to verify...")
                                                    verification = execute_script(script_path)
                                                    
                                                    if verification["success"]:
                                                        st.success("Script now works!")
                                                        if verification["stdout"]:
                                                            st.code(verification["stdout"], language="text")
                                                    else:
                                                        st.warning("Script still has errors")
                                                        st.code(verification["stderr"], language="text")
                                                else:
                                                    st.error("Failed to apply corrections")
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                                else:
                                    st.warning("Issue is external to code")
                                    st.info(analysis["not_related_to_code"])
                        
                        except Exception as e:
                            st.error(f"Debugging error: {e}")
    
    with tab2:
        st.subheader("Environment Details")
        
        if st.session_state.env_info:
            env = st.session_state.env_info
            
            st.markdown("**Python Information**")
            py_info = env["python_version"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Version", py_info["version"])
            with col2:
                st.caption(f"Path: {py_info['executable']}")
            
            st.divider()
            
            st.markdown("**Virtual Environments**")
            venv_info = env["virtual_env"]
            if venv_info["found"]:
                for venv in venv_info.get("venvs", []):
                    st.caption(f"**{venv['name']}** - {venv['path']}")
            else:
                st.caption("None detected")
            
            st.divider()
            
            st.markdown("**Package Managers**")
            pkg_info = env["package_manager"]
            if pkg_info["found"]:
                for mgr in pkg_info["managers"]:
                    st.caption(f"✓ {mgr}")
            else:
                st.caption("None detected")
            
            st.divider()
            
            st.markdown("**Dependencies**")
            req_info = env["requirements"]
            if req_info["found"]:
                st.caption(f"{req_info['count']} packages")
                with st.expander("View all"):
                    for pkg in req_info.get("packages", []):
                        st.code(pkg, language="text")
            else:
                st.caption("No requirements.txt")
    
    with tab3:
        st.subheader("Settings")
        
        st.markdown("**API Configuration**")
        
        env_key = os.getenv("GROQ_API_KEY")
        if env_key:
            st.success("GROQ_API_KEY is loaded from .env")
        else:
            groq_key = st.text_input(
                "Enter Groq API Key",
                type="password",
                help="Your Groq API key"
            )
            if st.button("Save API Key"):
                st.info("API key will be used for this session")

st.divider()
