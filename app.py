import cv2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.core.window import Window
from cpr_assistant import AdvancedCPRAssistant
from enums import CameraAngle

# Set initial window size
Window.size = (1280, 800)

# Load kv styling if available
try:
    Builder.load_file('cpr.kv')
except Exception:
    pass

class CPRControlPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (0.3, 1)
        self.padding = 10
        self.spacing = 10

        title = Label(
            text = '[b]CPR Assistant[/b]\nControl Panel',
            markup = True,
            size_hint = (1, 0.1),
            font_size = '20sp'
        )
        self.add_widget(title)

        self.status_label = Label(
            text = 'Status: Ready',
            size_hint = (1, 0.08),
            font_size = '16sp'
        )
        self.add_widget(self.status_label)

        self.mode_label = Label(
            text = 'Mode: Overhead Positioning',
            size_hint = (1, 0.08),
            font_size = '16sp',
            color = (0.2, 1, 0.2, 1)
        )
        self.add_widget(self.mode_label)

        self.metrics_layout = BoxLayout(orientation = 'vertical', size_hint = (1, 0.2))
        self.compression_label = Label(text = 'Compressions: 0', font_size = '14sp')
        self.rate_label = Label(text = 'Rate: 0/min', font_size = '14sp')
        self.accuracy_label = Label(text = 'Accuracy: 0%', font_size = '14sp')
        self.metrics_layout.add_widget(self.compression_label)
        self.metrics_layout.add_widget(self.rate_label)
        self.metrics_layout.add_widget(self.accuracy_label)
        self.add_widget(self.metrics_layout)

        self.start_btn = ToggleButton(
            text = 'Start Guidance',
            size_hint = (1, 0.1),
            font_size = '16sp'
        )
        self.add_widget(self.start_btn)

        mode_layout = GridLayout(cols=2, size_hint=(1, 0.1), spacing=5)
        self.overhead_btn = Button(
            text='Overhead Mode',
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.sideview_btn = Button(
            text='Side View Mode',
            background_normal=''
        )
        mode_layout.add_widget(self.overhead_btn)
        mode_layout.add_widget(self.sideview_btn)
        self.add_widget(mode_layout)
        
        action_layout = GridLayout(cols=2, size_hint=(1, 0.15), spacing=5)
        
        self.calibrate_btn = Button(
            text='Calibrate',
            background_color=(0.2, 0.6, 1, 1)
        )
        self.reset_btn = Button(
            text='Reset Counters',
            background_color=(1, 0.6, 0, 1)
        )
        self.emergency_btn = Button(
            text='🚨 Emergency Call',
            background_color=(1, 0.2, 0.2, 1)
        )
        
        action_layout.add_widget(self.calibrate_btn)
        action_layout.add_widget(self.reset_btn)
        self.add_widget(action_layout)
        self.add_widget(self.emergency_btn)
        
        self.feedback_label = Label(
            text='Position CPR recipient in frame',
            size_hint=(1, 0.15),
            font_size='14sp',
            text_size=(self.width * 0.9, None),
            halign='center',
            valign='middle'
        )
        self.add_widget(self.feedback_label)
        
        instructions = Label(
            text='[b]Instructions:[/b]\n'
                 '1. Choose camera angle\n'
                 '2. Start guidance\n'
                 '3. Follow on-screen feedback\n'
                 '4. Calibrate as needed',
            markup=True,
            size_hint=(1, 0.14),
            font_size='12sp',
            text_size=(self.width * 0.9, None),
            halign='left',
            valign='top'
        )
        self.add_widget(instructions)

class CPRApp(App):
    def build(self):
        self.title = 'CPR Hand Placement Assistant'
        
        main_layout = BoxLayout(orientation='horizontal')
        
        self.img = Image(size_hint=(0.7, 1))
        main_layout.add_widget(self.img)
        
        self.control_panel = CPRControlPanel()
        main_layout.add_widget(self.control_panel)
        
        self.assistant = AdvancedCPRAssistant()
        self.guidance_active = False
        self.current_frame = None
        
        self.control_panel.start_btn.bind(on_press=self.toggle_guidance)
        self.control_panel.overhead_btn.bind(on_press=self.switch_to_overhead)
        self.control_panel.sideview_btn.bind(on_press=self.switch_to_sideview)
        self.control_panel.calibrate_btn.bind(on_press=self.calibrate)
        self.control_panel.reset_btn.bind(on_press=self.reset_counters)
        self.control_panel.emergency_btn.bind(on_press=self.emergency_call)
        
        Clock.schedule_interval(self.update, 1.0/30.0)
        
        self.update_status_display()
        
        return main_layout
    
    def toggle_guidance(self, instance):
        self.guidance_active = instance.state == 'down'
        
        if self.guidance_active:
            self.control_panel.start_btn.text = 'Stop Guidance'
            self.control_panel.status_label.text = 'Status: Active'
            self.control_panel.status_label.color = (0.2, 1, 0.2, 1)
        else:
            self.control_panel.start_btn.text = 'Start Guidance'
            self.control_panel.status_label.text = 'Status: Paused'
            self.control_panel.status_label.color = (1, 0.6, 0, 1)
    
    def switch_to_overhead(self, instance):
        self.assistant.switch_angle(CameraAngle.OVERHEAD)
        self.control_panel.overhead_btn.background_color = (0.2, 0.8, 0.2, 1)
        self.control_panel.sideview_btn.background_color = (0.5, 0.5, 0.5, 1)
        self.update_status_display()
    
    def switch_to_sideview(self, instance):
        self.assistant.switch_angle(CameraAngle.SIDE_VIEW)
        self.control_panel.sideview_btn.background_color = (0.2, 0.8, 0.2, 1)
        self.control_panel.overhead_btn.background_color = (0.5, 0.5, 0.5, 1)
        self.update_status_display()
    
    def calibrate(self, instance):
        self.assistant.calibrate_current_mode()
        self.control_panel.feedback_label.text = 'Calibrated - Ready for guidance'
    
    def reset_counters(self, instance):
        self.assistant.reset_counters()
        self.update_metrics_display()
        self.control_panel.feedback_label.text = 'Counters reset'
        self.control_panel.feedback_label.color = (1, 1, 1, 1)
    
    def emergency_call(self, instance):
        self.assistant.emergency_call_simulation()
        self.control_panel.feedback_label.text = '🚨 EMERGENCY CALL INITIATED'
        self.control_panel.feedback_label.color = (1, 0, 0, 1)
    
    def update_status_display(self):
        if self.assistant.current_angle == CameraAngle.OVERHEAD:
            self.control_panel.mode_label.text = 'Mode: Overhead Positioning'
        else:
            self.control_panel.mode_label.text = 'Mode: Side View Compression'
    
    def update_metrics_display(self):
        analyzer = self.assistant.analyzer
        self.control_panel.compression_label.text = f'Compressions: {analyzer.compression_count}'
        self.control_panel.rate_label.text = f'Rate: {analyzer.current_rate:.0f}/min'
        
        if self.assistant.current_angle == CameraAngle.OVERHEAD:
            self.control_panel.accuracy_label.text = f'Position Accuracy: {analyzer.positioning_accuracy:.0f}%'
        else:
            self.control_panel.accuracy_label.text = f'Avg Depth: {analyzer.average_depth:.0f}px'
    
    def update(self, dt):
        frame = self.assistant.run()
        if frame is None:
            return
        
        # Update feedback and metrics when active; when paused, keep last feedback dimmed
        self.control_panel.feedback_label.text = self.assistant.last_feedback
        self.control_panel.feedback_label.color = (1, 1, 1, 1) if self.guidance_active else (0.8, 0.8, 0.8, 1)
        self.update_metrics_display()
        
        # Push frame to Kivy image
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img.texture = texture
    
    def on_stop(self):
        self.assistant.cleanup()

if __name__ == '__main__':
    CPRApp().run()