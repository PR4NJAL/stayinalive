from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

class LoginScreen(GridLayout):
    """Login screen for the CPR Assistant application"""
    
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.cols = 2
        self.add_widget(Label(text='User Name'))
        self.username = TextInput(multiline=False)
        self.add_widget(self.username)
        self.add_widget(Label(text='password'))
        self.password = TextInput(password=True, multiline=False)
        self.add_widget(self.password)
        
        # Add login button
        self.login_button = Button(text='Login')
        self.login_button.bind(on_press=self.on_login)
        self.add_widget(self.login_button)
        
        # Add placeholder for second column
        self.add_widget(Label(text=''))

    def on_login(self, instance):
        """Handle login button press"""
        username = self.username.text
        password = self.password.text
        
        if username and password:
            print(f"Login attempted: {username}")
            # Here you would typically validate credentials
            # For now, just print the attempt
        else:
            print("Please enter both username and password")

class CPRControlPanel(BoxLayout):
    """Control panel for CPR Assistant"""
    
    def __init__(self, cpr_assistant=None, **kwargs):
        super(CPRControlPanel, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.cpr_assistant = cpr_assistant
        
        # Mode selection buttons
        self.mode_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        self.overhead_btn = Button(text='Overhead Mode')
        self.overhead_btn.bind(on_press=self.switch_to_overhead)
        self.mode_layout.add_widget(self.overhead_btn)
        
        self.side_view_btn = Button(text='Side View Mode')
        self.side_view_btn.bind(on_press=self.switch_to_side_view)
        self.mode_layout.add_widget(self.side_view_btn)
        
        self.add_widget(self.mode_layout)
        
        # Control buttons
        self.control_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        self.start_btn = Button(text='Start Guidance')
        self.start_btn.bind(on_press=self.toggle_guidance)
        self.control_layout.add_widget(self.start_btn)
        
        self.reset_btn = Button(text='Reset')
        self.reset_btn.bind(on_press=self.reset_counters)
        self.control_layout.add_widget(self.reset_btn)
        
        self.add_widget(self.control_layout)
        
        # Status display
        self.status_label = Label(text='Status: Ready', size_hint_y=0.4)
        self.add_widget(self.status_label)
    
    def switch_to_overhead(self, instance):
        """Switch to overhead mode"""
        if self.cpr_assistant:
            self.cpr_assistant.switch_angle('overhead')
        self.status_label.text = 'Mode: Overhead (Positioning)'
    
    def switch_to_side_view(self, instance):
        """Switch to side view mode"""
        if self.cpr_assistant:
            self.cpr_assistant.switch_angle('side_view')
        self.status_label.text = 'Mode: Side View (Compression)'
    
    def toggle_guidance(self, instance):
        """Toggle guidance on/off"""
        if self.cpr_assistant:
            # This would need to be implemented in the CPR assistant
            pass
        self.status_label.text = 'Guidance: Toggled'
    
    def reset_counters(self, instance):
        """Reset all counters"""
        if self.cpr_assistant:
            self.cpr_assistant.reset_counters()
        self.status_label.text = 'Counters Reset'

class CPRApp(App):
    """Main Kivy application for CPR Assistant"""
    
    def build(self):
        return LoginScreen()
    
    def start_cpr_assistant(self):
        """Start the CPR assistant with UI"""
        # This would integrate with the CPR assistant
        pass

class CPRMainWindow(BoxLayout):
    """Main window combining login and CPR controls"""
    
    def __init__(self, **kwargs):
        super(CPRMainWindow, self).__init__(**kwargs)
        self.orientation = 'vertical'
        
        # Login screen
        self.login_screen = LoginScreen()
        self.login_screen.login_button.bind(on_press=self.on_login_success)
        self.add_widget(self.login_screen)
    
    def on_login_success(self, instance):
        """Handle successful login"""
        # Remove login screen and show CPR controls
        self.remove_widget(self.login_screen)
        
        # Add CPR control panel
        self.cpr_controls = CPRControlPanel()
        self.add_widget(self.cpr_controls)
