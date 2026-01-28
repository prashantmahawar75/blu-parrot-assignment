"""
Zepto Frida Hooking Script
Advanced method to intercept API calls directly from the Zepto Android app
Requires: Frida installed on PC and rooted Android device with frida-server
"""

import frida
import sys
import json
import time
from datetime import datetime

FRIDA_SCRIPT = """
// Hook OkHttp3 requests (common HTTP library in Android apps)
Java.perform(function() {
    console.log("[*] Frida script loaded successfully");
    
    // Hook OkHttp Response
    var Response = Java.use("okhttp3.Response");
    
    Response.body.implementation = function() {
        var body = this.body();
        var responseString = body.string();
        
        // Get URL
        var url = this.request().url().toString();
        
        // Log API responses
        if (url.indexOf("zepto") !== -1 || url.indexOf("api") !== -1) {
            console.log("[+] Intercepted Response");
            console.log("[URL] " + url);
            console.log("[BODY] " + responseString);
            console.log("[" + "=".repeat(60) + "]");
            
            // Send data to Python
            send({
                type: "api_response",
                url: url,
                body: responseString,
                timestamp: new Date().toISOString()
            });
        }
        
        // Return a new ResponseBody with the same content
        var MediaType = Java.use("okhttp3.MediaType");
        var ResponseBody = Java.use("okhttp3.ResponseBody");
        
        var contentType = body.contentType();
        var newBody = ResponseBody.create(contentType, responseString);
        
        return newBody;
    };
    
    // Hook Retrofit API calls (another common library)
    try {
        var Retrofit = Java.use("retrofit2.Retrofit");
        console.log("[*] Retrofit found, hooking...");
        
        Retrofit.baseUrl.overload().implementation = function() {
            var baseUrl = this.baseUrl();
            console.log("[Retrofit Base URL] " + baseUrl.toString());
            return baseUrl;
        };
    } catch(e) {
        console.log("[!] Retrofit not found or cannot be hooked");
    }
    
    // Hook common JSON parsing
    try {
        var JSONObject = Java.use("org.json.JSONObject");
        JSONObject.$init.overload('java.lang.String').implementation = function(json) {
            console.log("[JSON] Parsing: " + json.substring(0, 200) + "...");
            return this.$init(json);
        };
    } catch(e) {
        console.log("[!] JSONObject hooking failed");
    }
    
    console.log("[*] All hooks initialized");
});
"""


class FridaScraper:
    """
    Scraper using Frida to hook into the Zepto mobile app
    """
    
    def __init__(self, package_name: str = "com.grofers.customerapp"):

        self.package_name = package_name
        self.device = None
        self.session = None
        self.script = None
        self.captured_data = []
        
    def connect_device(self):

        try:
            # Get USB device
            self.device = frida.get_usb_device(timeout=10)
            print(f"[+] Connected to device: {self.device}")
            return True
        except Exception as e:
            print(f"[!] Failed to connect to device: {e}")
            print("[!] Make sure:")
            print("    1. Android device is connected via USB")
            print("    2. USB debugging is enabled")
            print("    3. frida-server is running on the device")
            return False
    
    def attach_to_app(self):

        try:
            print(f"[*] Attaching to {self.package_name}...")
            self.session = self.device.attach(self.package_name)
            print("[+] Successfully attached to app")
            return True
        except Exception as e:
            print(f"[!] Failed to attach to app: {e}")
            print("[!] Make sure the Zepto app is running on the device")
            return False
    
    def spawn_and_attach(self):

        try:
            print(f"[*] Spawning {self.package_name}...")
            pid = self.device.spawn([self.package_name])
            self.session = self.device.attach(pid)
            self.device.resume(pid)
            print(f"[+] Spawned and attached to app (PID: {pid})")
            return True
        except Exception as e:
            print(f"[!] Failed to spawn app: {e}")
            return False
    
    def on_message(self, message, data):

        if message['type'] == 'send':
            payload = message['payload']
            
            if payload.get('type') == 'api_response':
                print(f"\n[API Response Captured]")
                print(f"URL: {payload['url']}")
                print(f"Timestamp: {payload['timestamp']}")
                

                try:
                    body_json = json.loads(payload['body'])
                    print(f"Body: {json.dumps(body_json, indent=2)[:500]}...")
                    
                    self.captured_data.append({
                        'url': payload['url'],
                        'timestamp': payload['timestamp'],
                        'data': body_json
                    })
                except:
                    print(f"Body: {payload['body'][:200]}...")
                
                print("-" * 60)
        
        elif message['type'] == 'error':
            print(f"[!] Error: {message['stack']}")
    
    def inject_script(self):

        try:
            print("[*] Injecting Frida script...")
            self.script = self.session.create_script(FRIDA_SCRIPT)
            self.script.on('message', self.on_message)
            self.script.load()
            print("[+] Script injected successfully")
            return True
        except Exception as e:
            print(f"[!] Failed to inject script: {e}")
            return False
    
    def start_capture(self, duration: int = 300):

        print(f"\n[*] Capturing API calls for {duration} seconds...")
        print("[*] Use the Zepto app now to trigger API calls")
        print("[*] Navigate to the category you want to scrape")
        print()
        
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            print("\n[*] Capture interrupted by user")
    
    def save_captured_data(self, filename: str = None):

        if not self.captured_data:
            print("[!] No data captured")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"zepto_captured_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.captured_data, f, indent=2, ensure_ascii=False)
            
            print(f"[+] Saved {len(self.captured_data)} captured responses to {filename}")
        except Exception as e:
            print(f"[!] Failed to save data: {e}")
    
    def extract_products_from_captured_data(self):

        products = []
        
        for item in self.captured_data:
            data = item.get('data', {})
            
            if 'products' in data:
                products.extend(data['products'])
            elif 'data' in data and isinstance(data['data'], list):
                products.extend(data['data'])
            elif 'items' in data:
                products.extend(data['items'])
        
        print(f"[+] Extracted {len(products)} products from captured data")
        return products
    
    def run(self, attach_mode: bool = True, duration: int = 300):

        if not self.connect_device():
            return False
        
        if attach_mode:
            if not self.attach_to_app():
                return False
        else:
            if not self.spawn_and_attach():
                return False
        
        if not self.inject_script():
            return False
        
        self.start_capture(duration)
        
        self.save_captured_data()
        
        products = self.extract_products_from_captured_data()
        
        if products:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            products_file = f"zepto_products_{timestamp}.json"
            
            with open(products_file, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            
            print(f"[+] Saved extracted products to {products_file}")
        
        return True


def main():

    print("=" * 70)
    print("ZEPTO FRIDA SCRAPER - Advanced Mobile App Hooking")
    print("=" * 70)
    print()
    print("Prerequisites:")
    print("  1. Rooted Android device")
    print("  2. Frida installed (pip install frida-tools)")
    print("  3. frida-server running on Android device")
    print("  4. Zepto app installed on device")
    print("  5. USB debugging enabled")
    print()
    print("=" * 70)
    print()
    
    scraper = FridaScraper()
    
    print("Choose mode:")
    print("  1. Attach to running app (app must be open)")
    print("  2. Spawn new app instance")
    
    choice = input("\nEnter choice (1/2): ").strip()
    attach_mode = choice == "1"
    
    duration = input("\nCapture duration in seconds (default 300): ").strip()
    duration = int(duration) if duration.isdigit() else 300
    
    print()
    scraper.run(attach_mode=attach_mode, duration=duration)
    
    print("\n" + "=" * 70)
    print("Scraping completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
