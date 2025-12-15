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

def create_saml_auth_popup():
    """Create popup authentication that captures the auth token"""
    
    popup_html = f"""
    <div style="text-align: center; padding: 20px;">
        <button id="loginBtn" onclick="openAuthPopup()" 
                style="background: #1f4e79; color: white; padding: 12px 24px; 
                       border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">
            🚀 Login with SAML
        </button>
        
        <div id="authStatus" style="margin-top: 15px; padding: 10px; display: none;"></div>
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
            
            // Open popup for authentication
            const width = 900;
            const height = 700;
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
            
            startAuthMonitoring();
        }}
        
        function startAuthMonitoring() {{
            let checkCount = 0;
            const maxChecks = 300;
            
            authCheckInterval = setInterval(function() {{
                checkCount++;
                
                try {{
                    if (authWindow.closed) {{
                        clearInterval(authCheckInterval);
                        setTimeout(verifyAuthAndNotify, 1000);
                        return;
                    }}
                    
                    // Try to detect successful login
                    try {{
                        const popupUrl = authWindow.location.href;
                        if (popupUrl.includes('/MicroStrategyLibrary') && 
                            !popupUrl.includes('login') && 
                            !popupUrl.includes('auth')) {{
                            
                            clearInterval(authCheckInterval);
                            authWindow.close();
                            setTimeout(verifyAuthAndNotify, 1000);
                            return;
                        }}
                    }} catch (e) {{
                        // Expected cross-origin error during auth
                    }}
                    
                    if (checkCount >= maxChecks) {{
                        clearInterval(authCheckInterval);
                        document.getElementById('authStatus').innerHTML = 
                            '<div style="color: orange;">⚠️ Authentication timeout. Please try again.</div>';
                        resetButton();
                        if (authWindow && !authWindow.closed) authWindow.close();
                    }}
                    
                }} catch (e) {{
                    console.log('Auth check error:', e);
                }}
            }}, 1000);
        }}
        
        function verifyAuthAndNotify() {{
            const authStatus = document.getElementById('authStatus');
            authStatus.innerHTML = '<div style="color: #1f4e79;">🔍 Verifying authentication...</div>';
            
            // Test authentication by making a request to MicroStrategy API
            fetch('{MSTR_CONFIG["library_url"]}/api/sessions', {{
                method: 'GET',
                credentials: 'include',
                mode: 'cors'
            }})
            .then(response => {{
                if (response.ok) {{
                    authStatus.innerHTML = '<div style="color: green;">✅ Authentication successful! You can now load the dashboard.</div>';
                    
                    // Notify Streamlit that authentication succeeded
                    window.parent.postMessage({{
                        type: 'MSTR_AUTH_SUCCESS',
                        authenticated: true,
                        timestamp: new Date().getTime()
                    }}, '*');
                    
                }} else {{
                    authStatus.innerHTML = '<div style="color: red;">❌ Authentication failed. Please try again.</div>';
                    resetButton();
                }}
            }})
            .catch(error => {{
                authStatus.innerHTML = '<div style="color: red;">❌ Unable to verify authentication. Please try again.</div>';
                resetButton();
            }});
        }}
        
        function resetButton() {{
            const loginBtn = document.getElementById('loginBtn');
            loginBtn.disabled = false;
            loginBtn.innerHTML = '🚀 Login with SAML';
        }}
    </script>
    """
    
    return popup_html

def create_embedding_sdk_component():
    """Create MicroStrategy Embedding SDK component with hooks and listeners"""
    
    embed_html = f"""
    <div id="mstrDashboard" style="width: 100%; height: 700px; border: 1px solid #ddd; border-radius: 8px; position: relative;">
        <div id="loadingIndicator" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #666;">
            <div style="font-size: 18px;">🔄 Loading MicroStrategy Dashboard...</div>
            <div style="margin-top: 10px; font-size: 14px;">Initializing embedding SDK...</div>
        </div>
    </div>
    
    <!-- Event Log for Debugging -->
    <div id="eventLog" style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px; display: none;">
        <strong>Event Log:</strong>
        <div id="eventLogContent"></div>
    </div>
    
    <!-- Controls -->
    <div style="margin-top: 10px; text-align: center;">
        <button onclick="toggleEventLog()" style="padding: 5px 10px; margin: 0 5px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer;">
            Toggle Event Log
        </button>
        <button onclick="refreshDashboard()" style="padding: 5px 10px; margin: 0 5px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">
            Refresh Dashboard
        </button>
        <button onclick="exportPDF()" style="padding: 5px 10px; margin: 0 5px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer;">
            Export PDF
        </button>
    </div>
    
    <script src="{MSTR_CONFIG['library_url']}/javascript/embeddinglib.js"></script>
    <script>
        let mstrComponent = null;
        let eventLogVisible = false;
        
        // Event logging function
        function logEvent(event, data) {{
            const timestamp = new Date().toLocaleTimeString();
            const logContent = document.getElementById('eventLogContent');
            const logEntry = document.createElement('div');
            logEntry.innerHTML = `[${{timestamp}}] ${{event}}: ${{JSON.stringify(data) || 'No data'}}`;
            logContent.appendChild(logEntry);
            logContent.scrollTop = logContent.scrollHeight;
            
            // Also log to console
            console.log(`MSTR Event [${{event}}]:`, data);
            
            // Notify Streamlit of events
            window.parent.postMessage({{
                type: 'MSTR_EVENT',
                event: event,
                data: data,
                timestamp: timestamp
            }}, '*');
        }}
        
        function initializeMicroStrategy() {{
            logEvent('INIT_START', 'Initializing MicroStrategy Embedding SDK');
            
            try {{
                mstrComponent = microstrategy.embeddingComponent.create({{
                    serverUrl: "{MSTR_CONFIG['base_url']}",
                    
                    // Authentication handler
                    getAuthToken: function() {{
                        logEvent('AUTH_TOKEN_REQUEST', 'SDK requesting auth token');
                        // Return null to let MicroStrategy handle its own auth
                        return null;
                    }},
                    
                    placeholder: document.getElementById("mstrDashboard"),
                    
                    src: {{
                        libraryType: "document",
                        objectId: "{MSTR_CONFIG['object_id']}",
                        projectId: "{MSTR_CONFIG['project_id']}"
                    }},
                    
                    // Configuration options
                    enableResponsive: true,
                    navigationBar: {{
                        enabled: true,
                        gotoLibrary: true,
                        title: true,
                        toc: true
                    }},
                    
                    // Custom CSS
                    customCss: {{
                        fontFamily: "Arial, sans-serif"
                    }},
                    
                    // Event Handlers / Hooks
                    onLoad: function(data) {{
                        logEvent('LOAD', 'Dashboard loaded successfully');
                        document.getElementById('loadingIndicator').style.display = 'none';
                        
                        // Notify Streamlit
                        window.parent.postMessage({{
                            type: 'MSTR_DASHBOARD_LOADED',
                            success: true,
                            data: data
                        }}, '*');
                    }},
                    
                    onError: function(error) {{
                        logEvent('ERROR', error);
                        
                        const dashboard = document.getElementById('mstrDashboard');
                        dashboard.innerHTML = 
                            '<div style="text-align: center; padding: 50px; color: #dc3545;">' +
                            '<h3>🔐 Authentication Required</h3>' +
                            '<p>Please complete SAML authentication first using the login button above.</p>' +
                            '<p><strong>Error:</strong> ' + (error.message || JSON.stringify(error)) + '</p>' +
                            '<button onclick="initializeMicroStrategy()" style="margin-top: 15px; padding: 8px 16px; background: #1f4e79; color: white; border: none; border-radius: 4px; cursor: pointer;">Retry</button>' +
                            '</div>';
                        
                        // Notify Streamlit of error
                        window.parent.postMessage({{
                            type: 'MSTR_ERROR',
                            error: error
                        }}, '*');
                    }},
                    
                    onPageChange: function(data) {{
                        logEvent('PAGE_CHANGE', data);
                    }},
                    
                    onFilterChange: function(data) {{
                        logEvent('FILTER_CHANGE', data);
                    }},
                    
                    onSelectionChange: function(data) {{
                        logEvent('SELECTION_CHANGE', data);
                    }},
                    
                    onDrillDown: function(data) {{
                        logEvent('DRILL_DOWN', data);
                    }},
                    
                    onDrillUp: function(data) {{
                        logEvent('DRILL_UP', data);
                    }},
                    
                    onDataChange: function(data) {{
                        logEvent('DATA_CHANGE', data);
                    }}
                }});
                
                logEvent('INIT_COMPLETE', 'MicroStrategy component created successfully');
                
            }} catch (error) {{
                logEvent('INIT_ERROR', error);
                
                document.getElementById('mstrDashboard').innerHTML = 
                    '<div style="text-align: center; padding: 50px; color: #dc3545;">' +
                    '<h3>Initialization Error</h3>' +
                    '<p><strong>Error:</strong> ' + error.message + '</p>' +
                    '<button onclick="initializeMicroStrategy()" style="margin-top: 15px; padding: 8px 16px; background: #1f4e79; color: white; border: none; border-radius: 4px; cursor: pointer;">Retry</button>' +
                    '</div>';
            }}
        }}
        
        // Control functions
        function toggleEventLog() {{
            const eventLog = document.getElementById('eventLog');
            eventLogVisible = !eventLogVisible;
            eventLog.style.display = eventLogVisible ? 'block' : 'none';
        }}
        
        function refreshDashboard() {{
            logEvent('REFRESH_REQUEST', 'User requested dashboard refresh');
            if (mstrComponent) {{
                try {{
                    mstrComponent.refresh();
                    logEvent('REFRESH_SUCCESS', 'Dashboard refreshed');
                }} catch (error) {{
                    logEvent('REFRESH_ERROR', error);
                }}
            }} else {{
                initializeMicroStrategy();
            }}
        }}
        
        function exportPDF() {{
            logEvent('EXPORT_REQUEST', 'User requested PDF export');
            if (mstrComponent) {{
                try {{
                    mstrComponent.exportToPDF();
                    logEvent('EXPORT_SUCCESS', 'PDF export initiated');
                }} catch (error) {{
                    logEvent('EXPORT_ERROR', error);
                }}
            }}
        }}
        
        // Initialize when document is ready
        document.addEventListener('DOMContentLoaded', function() {{
            logEvent('DOM_READY', 'DOM loaded, starting initialization');
            setTimeout(initializeMicroStrategy, 500);
        }});
        
        // Listen for auth success messages
        window.addEventListener('message', function(event) {{
            if (event.data.type === 'AUTH_COMPLETE') {{
                logEvent('AUTH_SUCCESS_RECEIVED', 'Authentication success message received');
                setTimeout(initializeMicroStrategy, 1000);
            }}
        }});
    </script>
    """
    
    return embed_html

def main():
    st.set_page_config(
        page_title="MicroStrategy Dashboard with SDK",
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
        .section {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 MicroStrategy Dashboard with Embedding SDK</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication Section
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown("### 🔐 Step 1: SAML Authentication")
    st.info("Complete SAML authentication to enable dashboard access.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Authentication popup component
        popup_component = create_saml_auth_popup()
        components.html(popup_component, height=120)
    
    with col2:
        if st.button("✅ Authentication Complete", key="auth_complete"):
            st.session_state.authenticated = True
            st.session_state.show_dashboard = True
            st.success("🎉 Ready to load dashboard!")
            st.rerun()
        
        if st.session_state.authenticated:
            st.success("✅ Authenticated")
        else:
            st.warning("⏳ Waiting for authentication")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Dashboard Section
    if st.session_state.show_dashboard:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("### 📈 Step 2: Interactive Dashboard")
        
        # Control buttons
        col1, col2, col3 = st.columns([6, 1, 1])
        with col2:
            if st.button("🔄 Reload SDK", key="reload_sdk"):
                st.rerun()
        with col3:
            if st.button("🚪 Reset", key="reset_app"):
                st.session_state.authenticated = False
                st.session_state.show_dashboard = False
                st.rerun()
        
        # MicroStrategy Embedding SDK Component
        st.info("Dashboard with full SDK integration - includes event hooks, listeners, and interactive controls")
        
        embedding_component = create_embedding_sdk_component()
        components.html(embedding_component, height=900)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SDK Features Info
        with st.expander("🛠️ SDK Features & Event Hooks"):
            st.markdown("""
            **Available Event Hooks:**
            - `onLoad`: Dashboard loaded successfully
            - `onError`: Error handling and authentication prompts
            - `onPageChange`: User navigates between pages
            - `onFilterChange`: Filter selections change
            - `onSelectionChange`: User selects data points
            - `onDrillDown/onDrillUp`: Drill-down operations
            - `onDataChange`: Data refreshes or updates
            
            **Interactive Controls:**
            - **Toggle Event Log**: View real-time events
            - **Refresh Dashboard**: Reload dashboard data
            - **Export PDF**: Export current view to PDF
            
            **SDK Methods Available:**
            ```javascript
            mstrComponent.refresh()        // Refresh data
            mstrComponent.exportToPDF()    // Export to PDF
            mstrComponent.applyFilter()    // Apply filters programmatically
            mstrComponent.selectElement()  // Select elements
            ```
            """)
    
    else:
        st.info("👆 Please complete SAML authentication above to access the dashboard with full SDK integration.")

if __name__ == "__main__":
    main()
