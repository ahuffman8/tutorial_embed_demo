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
    
    def initiate_saml_login(self):
        """Initiate SAML authentication flow"""
        try:
            # Get SAML login URL from MicroStrategy
            saml_url = f"{self.library_url}/api/auth/saml"
            
            # For tutorial environment, we might need to handle this differently
            # This would typically redirect to the SAML IdP
            login_url = f"{self.library_url}/#/login"
            
            return {"success": True, "login_url": login_url}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_session(self, session_token=None):
        """Validate if user has active session"""
        try:
            # Check session validity
            response = requests.get(f"{self.library_url}/api/sessions", 
                                  cookies={'X-MSTR-AuthToken': session_token} if session_token else None)
            
            if response.status_code == 200:
                return {"success": True, "token": session_token}
            else:
                return {"success": False}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

def create_saml_login_component():
    """Create SAML login component that handles the auth flow"""
    
    login_html = f"""
    <div style="width: 100%; height: 500px; border: 1px solid #ddd; border-radius: 8px;">
        <iframe 
            id="samlFrame"
            src="{MSTR_CONFIG['library_url']}/#/login"
            style="width: 100%; height: 100%; border: none; border-radius: 8px;"
            onload="handleFrameLoad()"
        ></iframe>
    </div>
    
    <script>
        let authCheckInterval;
        
        function handleFrameLoad() {{
            console.log('SAML frame loaded');
            startAuthCheck();
        }}
        
        function startAuthCheck() {{
            authCheckInterval = setInterval(checkAuthStatus, 2000);
        }}
        
        function checkAuthStatus() {{
            try {{
                // Try to access the iframe content to check if auth completed
                const frame = document.getElementById('samlFrame');
                const frameDoc = frame.contentDocument || frame.contentWindow.document;
                
                // Check if we're back at the main library page (auth successful)
                if (frameDoc.location.href.includes('/{MSTR_CONFIG['project_id']}')) {{
                    clearInterval(authCheckInterval);
                    
                    // Extract auth token from cookies or session
                    fetch('{MSTR_CONFIG['library_url']}/api/sessions', {{
                        credentials: 'include'
                    }})
                    .then(response => {{
                        if (response.ok) {{
                            // Notify Streamlit that auth is complete
                            window.parent.postMessage({{
                                type: 'SAML_AUTH_SUCCESS',
                                token: 'authenticated'
                            }}, '*');
                        }}
                    }});
                }}
            }} catch (e) {{
                // Cross-origin restriction - normal for SAML flow
                console.log('Checking auth status...');
            }}
        }}
        
        // Listen for successful navigation in iframe
        window.addEventListener('message', function(event) {{
            if (event.data.type === 'AUTH_SUCCESS') {{
                clearInterval(authCheckInterval);
                window.parent.postMessage({{
                    type: 'SAML_AUTH_SUCCESS',
                    token: event.data.token
                }}, '*');
            }}
        }});
    </script>
    """
    
    return login_html

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
                        // Return session token - in production you'd get this from authentication
                        return window.mstrAuthToken || '';
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
        
        // Set auth token when available
        function setAuthToken(token) {{
            window.mstrAuthToken = token;
        }}
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
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None
    
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
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 MicroStrategy Tutorial Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        # Login Screen
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown("### 🔐 SAML Authentication Required")
        st.info("Please log in using your SAML credentials to access the MicroStrategy dashboard.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Method 1: Direct redirect approach
            if st.button("🚀 Login with SAML", key="saml_login", use_container_width=True):
                # Redirect to SAML login
                login_url = f"{MSTR_CONFIG['library_url']}/#/login"
                st.markdown(f"""
                <script>
                    window.open('{login_url}', '_blank');
                </script>
                """, unsafe_allow_html=True)
                st.success("Please complete login in the new tab, then return here and click 'Check Authentication'")
            
            st.markdown("---")
            
            # Method 2: Embedded login
            st.markdown("#### Or login directly below:")
            
            # Create embedded SAML login
            login_component = create_saml_login_component()
            components.html(login_component, height=520)
            
            st.markdown("---")
            
            # Manual auth check button
            if st.button("✅ Check Authentication Status", key="check_auth"):
                auth = MicroStrategySAMLAuth()
                result = auth.validate_session()
                
                if result.get("success"):
                    st.session_state.authenticated = True
                    st.session_state.auth_token = result.get("token", "authenticated")
                    st.success("🎉 Authentication successful! Loading dashboard...")
                    st.rerun()
                else:
                    st.warning("Authentication not complete. Please ensure you've logged in successfully.")
            
            # Demo mode for testing
            st.markdown("---")
            st.markdown("##### For Testing:")
            if st.button("🧪 Demo Mode (Skip Auth)", key="demo_mode"):
                st.session_state.authenticated = True
                st.session_state.auth_token = "demo_token"
                st.success("Demo mode activated!")
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Instructions
        with st.expander("ℹ️ Login Instructions"):
            st.markdown("""
            **How to login:**
            
            1. **Option 1 - New Tab Login:**
               - Click "Login with SAML" button
               - Complete authentication in the new tab
               - Return here and click "Check Authentication Status"
            
            2. **Option 2 - Embedded Login:**
               - Use the login form above
               - Complete the SAML authentication
               - The page will automatically detect successful login
            
            **Troubleshooting:**
            - If login doesn't work, try refreshing the page
            - Ensure pop-ups are enabled in your browser
            - Contact your administrator if you continue to have issues
            """)
    
    else:
        # Dashboard Screen
        st.success(f"🎉 Welcome! You are successfully authenticated.")
        
        # Logout button in the corner
        col1, col2, col3 = st.columns([6, 1, 1])
        with col3:
            if st.button("🚪 Logout", key="logout"):
                st.session_state.authenticated = False
                st.session_state.auth_token = None
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
