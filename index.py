import streamlit as st
import requests
import json
from urllib.parse import quote, urlencode
import streamlit.components.v1 as components
import base64

# Configuration for MicroStrategy Tutorial Environment
MSTR_CONFIG = {
    "base_url": "https://tutorial.microstrategy.com",
    "project_id": "B7CA92F04B9FAE8D941C3E9B7E0CD754",
    "object_id": "152C22B1284EF1253585CA9B0FEE89E9",
    "library_url": "https://tutorial.microstrategy.com/MicroStrategyLibrary"
}

class MicroStrategySAMLAuth:
    def __init__(self):
        self.base_url = MSTR_CONFIG["base_url"]
        self.library_url = MSTR_CONFIG["library_url"]
    
    def validate_session(self):
        """Check if user has active session by testing API access"""
        try:
            # Test API endpoint that requires authentication
            test_url = f"{self.library_url}/api/projects"
            response = requests.get(test_url, timeout=10)
            
            # If we get a 200, user is authenticated
            if response.status_code == 200:
                return {"success": True, "authenticated": True}
            # If we get 401, user needs to authenticate  
            elif response.status_code == 401:
                return {"success": True, "authenticated": False}
            else:
                return {"success": False, "error": f"Unexpected response: {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

def create_saml_login_iframe():
    """Create an iframe for SAML login"""
    
    iframe_html = f"""
    <div style="width: 100%; height: 600px; border: 2px solid #ddd; border-radius: 8px; overflow: hidden;">
        <iframe 
            id="samlLoginFrame"
            src="{MSTR_CONFIG['library_url']}"
            style="width: 100%; height: 100%; border: none;"
            sandbox="allow-same-origin allow-scripts allow-forms allow-top-navigation allow-popups"
        ></iframe>
    </div>
    
    <div style="margin-top: 10px; padding: 10px; background: #f0f2f6; border-radius: 5px; font-size: 14px;">
        <strong>Instructions:</strong>
        <ol style="margin: 5px 0; padding-left: 20px;">
            <li>If you see a login page above, enter your SAML credentials</li>
            <li>After successful login, you should see the MicroStrategy library</li>
            <li>Once logged in, click "Check Authentication" below</li>
        </ol>
    </div>
    """
    
    return iframe_html

def create_mstr_dashboard():
    """Create the embedded MicroStrategy dashboard"""
    
    embed_html = f"""
    <div id="mstrDashboard" style="width: 100%; height: 700px; border: 1px solid #ddd; border-radius: 8px;"></div>
    
    <script src="{MSTR_CONFIG['library_url']}/javascript/embeddinglib.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Initializing MicroStrategy embedding...');
            
            try {{
                microstrategy.embeddingComponent.create({{
                    serverUrl: "{MSTR_CONFIG['base_url']}",
                    getAuthToken: function() {{
                        // For SAML environments, the token is often managed by cookies
                        // Return empty string to use existing session
                        return '';
                    }},
                    placeholder: document.getElementById("mstrDashboard"),
                    src: {{
                        libraryType: "document",
                        objectId: "{MSTR_CONFIG['object_id']}",
                        projectId: "{MSTR_CONFIG['project_id']}"
                    }},
                    enableResponsive: true,
                    navigationBar: {{
                        enabled: true,
                        gotoLibrary: true,
                        title: true
                    }},
                    customCss: {{
                        fontFamily: "Arial, sans-serif"
                    }},
                    onError: function(error) {{
                        console.error('MicroStrategy embedding error:', error);
                        document.getElementById("mstrDashboard").innerHTML = 
                            '<div style="text-align: center; padding: 50px; color: #666;">' +
                            '<h3>🔐 Authentication Required</h3>' +
                            '<p>Please ensure you are logged in to MicroStrategy.</p>' +
                            '<p>Error details: ' + JSON.stringify(error) + '</p>' +
                            '</div>';
                    }}
                }});
                
                console.log('MicroStrategy component created successfully');
                
            }} catch (error) {{
                console.error("Error creating MicroStrategy component:", error);
                document.getElementById("mstrDashboard").innerHTML = 
                    '<div style="text-align: center; padding: 50px; color: #666;">' +
                    '<h3>Unable to load dashboard</h3>' +
                    '<p>Error: ' + error.message + '</p>' +
                    '<p>Please try refreshing the page or contact support.</p>' +
                    '</div>';
            }}
        }});
    </script>
    """
    
    return embed_html

def main():
    st.set_page_config(
        page_title="MicroStrategy Tutorial Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'auth_checked' not in st.session_state:
        st.session_state.auth_checked = False
    
    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .main-header h1 {
            color: white;
            margin: 0;
            text-align: center;
        }
        .login-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .auth-button {
            background: #1f4e79;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem;
            text-align: center;
        }
        .auth-button:hover {
            background: #2d5aa0;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 MicroStrategy Tutorial Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-check authentication on first load
    if not st.session_state.auth_checked:
        with st.spinner("Checking authentication status..."):
            auth = MicroStrategySAMLAuth()
            result = auth.validate_session()
            
            if result.get("success") and result.get("authenticated"):
                st.session_state.authenticated = True
                st.success("✅ Already authenticated! Loading dashboard...")
            
            st.session_state.auth_checked = True
            st.rerun()
    
    if not st.session_state.authenticated:
        # Login Screen
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown("### 🔐 SAML Authentication Required")
        st.info("Please log in using your SAML credentials to access the MicroStrategy dashboard.")
        
        # Method 1: Direct link (replaces the broken JavaScript approach)
        st.markdown("#### Option 1: Login in New Tab")
        login_url = f"{MSTR_CONFIG['library_url']}"
        
        st.markdown(f"""
        **Step 1:** Click this link to open MicroStrategy login in a new tab:
        
        <a href="{login_url}" target="_blank" class="auth-button">🚀 Open MicroStrategy Login</a>
        
        **Step 2:** Complete your SAML authentication in that tab
        
        **Step 3:** Return here and click the button below to continue
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if st.button("✅ I've Logged In - Continue", key="check_auth_manual", use_container_width=True):
                with st.spinner("Verifying authentication..."):
                    auth = MicroStrategySAMLAuth()
                    result = auth.validate_session()
                    
                    if result.get("success") and result.get("authenticated"):
                        st.session_state.authenticated = True
                        st.success("🎉 Authentication verified! Loading dashboard...")
                        st.rerun()
                    else:
                        st.error("❌ Authentication not detected. Please ensure you completed the login process.")
                        st.info("Try refreshing the login tab and completing the authentication again.")
        
        st.markdown("---")
        
        # Method 2: Embedded login
        st.markdown("#### Option 2: Login Below (Embedded)")
        st.info("Complete your SAML authentication in the frame below, then click 'Check Authentication'")
        
        # Create embedded login iframe
        iframe_component = create_saml_login_iframe()
        components.html(iframe_component, height=650)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("✅ Check Authentication Status", key="check_auth_iframe", use_container_width=True):
                with st.spinner("Checking authentication..."):
                    auth = MicroStrategySAMLAuth()
                    result = auth.validate_session()
                    
                    if result.get("success") and result.get("authenticated"):
                        st.session_state.authenticated = True
                        st.success("🎉 Authentication successful! Loading dashboard...")
                        st.rerun()
                    else:
                        st.warning("Authentication not complete. Please ensure you've logged in successfully in the frame above.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Troubleshooting section
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **If authentication isn't working:**
            
            1. **Browser Issues:**
               - Try disabling ad blockers
               - Enable third-party cookies
               - Clear browser cache and cookies
            
            2. **Login Process:**
               - Make sure you complete the entire SAML flow
               - Look for the MicroStrategy library interface after login
               - Don't close the login tab until you see the main interface
            
            3. **Still having issues?**
               - Try refreshing this entire page
               - Use a different browser
               - Contact your system administrator
            
            **Debug Information:**
            - Login URL: `{login_url}`
            - Expected after login: You should see the MicroStrategy Library interface
            """)
            
            # Add a debug check button
            if st.button("🔍 Debug - Check Current Status"):
                auth = MicroStrategySAMLAuth()
                result = auth.validate_session()
                st.json({
                    "Authentication Check": result,
                    "Expected Login URL": login_url,
                    "Session State": {
                        "authenticated": st.session_state.authenticated,
                        "auth_checked": st.session_state.auth_checked
                    }
                })
    
    else:
        # Dashboard Screen
        st.success(f"🎉 Welcome! You are successfully authenticated.")
        
        # Logout and refresh buttons
        col1, col2, col3 = st.columns([5, 1, 1])
        with col2:
            if st.button("🔄 Refresh Auth", key="refresh_auth"):
                st.session_state.auth_checked = False
                st.rerun()
        with col3:
            if st.button("🚪 Logout", key="logout"):
                st.session_state.authenticated = False
                st.session_state.auth_checked = False
                st.info("Logged out. Note: You may need to close your browser to fully log out of SAML.")
                st.rerun()
        
        st.markdown("---")
        
        # Embedded Dashboard
        st.markdown("### 📈 Your Dashboard")
        
        dashboard_html = create_mstr_dashboard()
        components.html(dashboard_html, height=720)
        
        # Dashboard info
        with st.expander("📋 Dashboard Information"):
            st.json({
                "Environment": "MicroStrategy Tutorial",
                "Project ID": MSTR_CONFIG["project_id"],
                "Object ID": MSTR_CONFIG["object_id"], 
                "Base URL": MSTR_CONFIG["base_url"]
            })

if __name__ == "__main__":
    main()
