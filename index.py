import streamlit as st
import requests
import json
from urllib.parse import quote, urlencode
import streamlit.components.v1 as components
import time

# Configuration for MicroStrategy Tutorial Environment
MSTR_CONFIG = {
    "base_url": "https://tutorial.microstrategy.com",
    "project_id": "B7CA92F04B9FAE8D941C3E9B7E0CD754",
    "object_id": "152C22B1284EF1253585CA9B0FEE89E9",
    "library_url": "https://tutorial.microstrategy.com/MicroStrategyLibrary"
}

def create_auth_popup_component():
    """Create a popup-based authentication system that can communicate back"""
    
    popup_html = f"""
    <div style="text-align: center; padding: 20px;">
        <button id="loginBtn" onclick="openAuthPopup()" 
                style="background: #1f4e79; color: white; padding: 12px 24px; 
                       border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">
            🚀 Login with SAML
        </button>
        
        <div id="authStatus" style="margin-top: 15px; padding: 10px; display: none;"></div>
        
        <div style="margin-top: 20px; padding: 15px; background: #f0f2f6; border-radius: 5px; font-size: 14px;">
            <strong>How it works:</strong>
            <ol style="text-align: left; margin: 10px 0;">
                <li>Click "Login with SAML" to open authentication popup</li>
                <li>Complete your SAML login in the popup window</li>
                <li>The popup will automatically close when authentication is complete</li>
                <li>This page will automatically detect the successful authentication</li>
            </ol>
        </div>
    </div>
    
    <script>
        let authWindow = null;
        let authCheckInterval = null;
        
        function openAuthPopup() {{
            const loginBtn = document.getElementById('loginBtn');
            const authStatus = document.getElementById('authStatus');
            
            loginBtn.disabled = true;
            loginBtn.innerHTML = '⏳ Opening login window...';
            
            authStatus.style.display = 'block';
            authStatus.innerHTML = '<div style="color: #1f4e79;">📝 Please complete authentication in the popup window...</div>';
            
            // Open popup window
            const width = 800;
            const height = 600;
            const left = (screen.width - width) / 2;
            const top = (screen.height - height) / 2;
            
            authWindow = window.open(
                '{MSTR_CONFIG["library_url"]}',
                'mstr_auth',
                `width=${{width}},height=${{height}},left=${{left}},top=${{top}},scrollbars=yes,resizable=yes`
            );
            
            if (!authWindow) {{
                authStatus.innerHTML = '<div style="color: red;">❌ Popup blocked! Please allow popups and try again.</div>';
                resetButton();
                return;
            }}
            
            // Start monitoring the popup
            startAuthMonitoring();
        }}
        
        function startAuthMonitoring() {{
            let checkCount = 0;
            const maxChecks = 300; // 5 minutes max
            
            authCheckInterval = setInterval(function() {{
                checkCount++;
                
                try {{
                    // Check if popup is closed
                    if (authWindow.closed) {{
                        clearInterval(authCheckInterval);
                        
                        // Give a moment for cookies to be set, then check auth
                        setTimeout(checkAuthenticationStatus, 1000);
                        return;
                    }}
                    
                    // Try to detect successful login by checking the URL
                    try {{
                        const popupUrl = authWindow.location.href;
                        
                        // Check if we're at the main library page (indicates successful login)
                        if (popupUrl.includes('/MicroStrategyLibrary') && 
                            !popupUrl.includes('login') && 
                            !popupUrl.includes('auth')) {{
                            
                            clearInterval(authCheckInterval);
                            
                            // Close the popup
                            authWindow.close();
                            
                            // Check authentication
                            setTimeout(checkAuthenticationStatus, 1000);
                            return;
                        }}
                    }} catch (e) {{
                        // Cross-origin error is expected during auth flow
                    }}
                    
                    // Timeout check
                    if (checkCount >= maxChecks) {{
                        clearInterval(authCheckInterval);
                        document.getElementById('authStatus').innerHTML = 
                            '<div style="color: orange;">⚠️ Authentication timeout. Please try again.</div>';
                        resetButton();
                        
                        if (authWindow && !authWindow.closed) {{
                            authWindow.close();
                        }}
                    }}
                    
                }} catch (e) {{
                    // Handle any errors
                    console.log('Auth check error:', e);
                }}
            }}, 1000);
        }}
        
        function checkAuthenticationStatus() {{
            const authStatus = document.getElementById('authStatus');
            authStatus.innerHTML = '<div style="color: #1f4e79;">🔍 Verifying authentication...</div>';
            
            // Test authentication by trying to access a MicroStrategy API endpoint
            fetch('{MSTR_CONFIG["library_url"]}/api/sessions', {{
                method: 'GET',
                credentials: 'include',
                mode: 'cors'
            }})
            .then(response => {{
                if (response.ok || response.status === 200) {{
                    // Authentication successful
                    authStatus.innerHTML = '<div style="color: green;">✅ Authentication successful! Loading dashboard...</div>';
                    
                    // Notify Streamlit that authentication is complete
                    window.parent.postMessage({{
                        type: 'MSTR_AUTH_SUCCESS',
                        authenticated: true,
                        timestamp: new Date().getTime()
                    }}, '*');
                    
                }} else if (response.status === 401) {{
                    // Not authenticated
                    authStatus.innerHTML = '<div style="color: red;">❌ Authentication failed. Please try again.</div>';
                    resetButton();
                }} else {{
                    // Other error
                    authStatus.innerHTML = '<div style="color: orange;">⚠️ Unable to verify authentication. Please try refreshing the page.</div>';
                    resetButton();
                }}
            }})
            .catch(error => {{
                console.error('Auth check error:', error);
                authStatus.innerHTML = '<div style="color: red;">❌ Authentication check failed. Please try again.</div>';
                resetButton();
            }});
        }}
        
        function resetButton() {{
            const loginBtn = document.getElementById('loginBtn');
            loginBtn.disabled = false;
            loginBtn.innerHTML = '🚀 Login with SAML';
        }}
        
        // Listen for messages from popup or parent
        window.addEventListener('message', function(event) {{
            if (event.data.type === 'MSTR_AUTH_COMPLETE') {{
                clearInterval(authCheckInterval);
                checkAuthenticationStatus();
            }}
        }});
    </script>
    """
    
    return popup_html

def create_direct_auth_iframe():
    """Create an iframe that handles authentication and embedding in one"""
    
    iframe_html = f"""
    <div style="width: 100%; height: 700px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <iframe 
            id="mstrDirectFrame"
            src="{MSTR_CONFIG['library_url']}/app/{MSTR_CONFIG['project_id']}/{MSTR_CONFIG['object_id']}"
            style="width: 100%; height: 100%; border: none;"
            sandbox="allow-same-origin allow-scripts allow-forms allow-top-navigation allow-popups allow-popups-to-escape-sandbox"
        ></iframe>
    </div>
    
    <div style="margin-top: 10px; padding: 10px; background: #e8f4fd; border-radius: 5px; font-size: 14px;">
        <strong>ℹ️ Instructions:</strong>
        <ul style="margin: 5px 0; padding-left: 20px;">
            <li>If you see a login page, complete your SAML authentication</li>
            <li>After login, your dashboard will load automatically</li>
            <li>If you encounter issues, try the popup method above</li>
        </ul>
    </div>
    """
    
    return iframe_html

def create_mstr_dashboard_embedded():
    """Create embedded dashboard that handles its own auth"""
    
    embed_html = f"""
    <div id="mstrContainer" style="width: 100%; height: 700px; border: 1px solid #ddd; border-radius: 8px;"></div>
    
    <script src="{MSTR_CONFIG['library_url']}/javascript/embeddinglib.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Initializing MicroStrategy embedding with authentication...');
            
            try {{
                microstrategy.embeddingComponent.create({{
                    serverUrl: "{MSTR_CONFIG['base_url']}",
                    getAuthToken: function() {{
                        // Let MicroStrategy handle its own authentication
                        return null;
                    }},
                    placeholder: document.getElementById("mstrContainer"),
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
                        
                        // If it's an auth error, show login prompt
                        if (error.code === 'ERR_AUTH_FAILED' || error.message.includes('auth')) {{
                            document.getElementById("mstrContainer").innerHTML = 
                                '<div style="text-align: center; padding: 50px; color: #666;">' +
                                '<h3>🔐 Authentication Required</h3>' +
                                '<p>Please use one of the authentication methods above to log in first.</p>' +
                                '<button onclick="window.location.reload()" style="margin-top: 15px; padding: 8px 16px; background: #1f4e79; color: white; border: none; border-radius: 4px; cursor: pointer;">Refresh Page</button>' +
                                '</div>';
                        }} else {{
                            document.getElementById("mstrContainer").innerHTML = 
                                '<div style="text-align: center; padding: 50px; color: #666;">' +
                                '<h3>Unable to load dashboard</h3>' +
                                '<p>Error: ' + error.message + '</p>' +
                                '<button onclick="window.location.reload()" style="margin-top: 15px; padding: 8px 16px; background: #1f4e79; color: white; border: none; border-radius: 4px; cursor: pointer;">Retry</button>' +
                                '</div>';
                        }}
                    }},
                    onLoad: function() {{
                        console.log('MicroStrategy dashboard loaded successfully');
                        
                        // Notify Streamlit that the dashboard is ready
                        window.parent.postMessage({{
                            type: 'MSTR_DASHBOARD_LOADED',
                            success: true
                        }}, '*');
                    }}
                }});
                
            }} catch (error) {{
                console.error("Error creating MicroStrategy component:", error);
                document.getElementById("mstrContainer").innerHTML = 
                    '<div style="text-align: center; padding: 50px; color: #666;">' +
                    '<h3>Initialization Error</h3>' +
                    '<p>Error: ' + error.message + '</p>' +
                    '<button onclick="window.location.reload()" style="margin-top: 15px; padding: 8px 16px; background: #1f4e79; color: white; border: none; border-radius: 4px; cursor: pointer;">Refresh Page</button>' +
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
    if 'show_dashboard' not in st.session_state:
        st.session_state.show_dashboard = False
    
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
        .auth-section {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            border-left: 4px solid #1f4e79;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 MicroStrategy Tutorial Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for authentication messages from JavaScript
    if st.query_params.get("auth") == "success":
        st.session_state.authenticated = True
        st.session_state.show_dashboard = True
    
    # Authentication Section
    st.markdown('<div class="auth-section">', unsafe_allow_html=True)
    st.markdown("### 🔐 Authentication Options")
    
    tab1, tab2, tab3 = st.tabs(["🚀 Popup Login", "🖼️ Direct Embed", "📱 Manual Process"])
    
    with tab1:
        st.markdown("**Recommended:** This method opens authentication in a popup and automatically detects success.")
        
        # Popup authentication component
        popup_component = create_auth_popup_component()
        popup_result = components.html(popup_component, height=200)
        
        # Listen for authentication success messages
        if st.button("✅ I completed popup authentication", key="popup_success"):
            st.session_state.authenticated = True
            st.session_state.show_dashboard = True
            st.success("🎉 Great! Loading your dashboard...")
            st.rerun()
    
    with tab2:
        st.markdown("**Alternative:** Direct embedding that handles authentication within the frame.")
        st.info("This will show either the login page or your dashboard directly below.")
        
        # Direct iframe embed
        direct_embed = create_direct_auth_iframe()
        components.html(direct_embed, height=720)
        
        st.success("✅ If you can see your dashboard above, you're all set!")
    
    with tab3:
        st.markdown("**Manual Process:** If the other methods don't work.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            login_url = f"{MSTR_CONFIG['library_url']}/app/{MSTR_CONFIG['project_id']}/{MSTR_CONFIG['object_id']}"
            st.markdown(f"""
            **Step 1:** Open this link in a new tab:
            
            <a href="{login_url}" target="_blank" style="background: #1f4e79; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px;">Open Dashboard</a>
            """, unsafe_allow_html=True)
            
            st.markdown("**Step 2:** Complete authentication in that tab")
            st.markdown("**Step 3:** Click the button below")
        
        with col2:
            if st.button("🎯 Show Dashboard Here", key="manual_success", use_container_width=True):
                st.session_state.show_dashboard = True
                st.success("Loading dashboard...")
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Dashboard Section
    if st.session_state.show_dashboard:
        st.markdown("---")
        st.markdown("### 📈 Your MicroStrategy Dashboard")
        
        # Control buttons
        col1, col2, col3 = st.columns([6, 1, 1])
        with col2:
            if st.button("🔄 Refresh", key="refresh_dashboard"):
                st.rerun()
        with col3:
            if st.button("🚪 Reset", key="reset_app"):
                st.session_state.authenticated = False
                st.session_state.show_dashboard = False
                st.rerun()
        
        # Embedded Dashboard
        dashboard_html = create_mstr_dashboard_embedded()
        components.html(dashboard_html, height=720)
        
        # Info section
        with st.expander("📋 Dashboard Information"):
            st.json({
                "Environment": "MicroStrategy Tutorial",
                "Project ID": MSTR_CONFIG["project_id"],
                "Object ID": MSTR_CONFIG["object_id"],
                "Dashboard URL": f"{MSTR_CONFIG['library_url']}/app/{MSTR_CONFIG['project_id']}/{MSTR_CONFIG['object_id']}"
            })

if __name__ == "__main__":
    main()
