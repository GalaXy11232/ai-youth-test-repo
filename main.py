import customtkinter as cTk
from PIL import Image, ImageTk
import re
import easyocr
import openfoodfacts 
import tkinter.filedialog
import os

# --- CONSTANTS ---
EASYOCR_LANGUAGES = ['ro'] 

OFF_COMMON_ALLERGENS = ["lapte", "soia", "gluten", "alune", "ouă", "lactoză"] 
BAD_INGREDIENTS = {"zahăr", "benzoat de sodiu", "monoglutamat de sodiu", "sirop de porumb", "ulei hidrogenat"}

## Savefile into local data folder
SAVEFILE_NAME = 'allergens_save.data'
SAVEFILE_DIRPATH = os.environ['USERPROFILE'] + '\\Appdata\\Local\\NutriLabel\\'
SAVEFILE_PATH = SAVEFILE_DIRPATH + SAVEFILE_NAME
os.mkdir(SAVEFILE_DIRPATH) if not os.path.exists(SAVEFILE_DIRPATH) else None
# ---------------------


# --- 1. CORE ANALYSIS FUNCTIONS ---
def remove_diacritics(text):
    replace = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'
    }

    for diacr, repl in replace.items():
        text = text.replace(diacr, repl)
    
    return text

## Preremove diacritics (yes it's outside the function womp womp)
OFF_COMMON_ALLERGENS = [remove_diacritics(a) for a in OFF_COMMON_ALLERGENS]
BAD_INGREDIENTS = {remove_diacritics(a) for a in BAD_INGREDIENTS}


def parse_ingredients(ocr_text):
    """Cleans raw OCR text and attempts to split it into a list of ingredients."""
    cleaned_text = ocr_text.lower().replace('\n', ' ').strip()
    
    # Simple heuristic to find the ingredient list
    if "ingredients:" in cleaned_text:
        ingredient_part = cleaned_text.split("ingredients:", 1)[1]
    else:
        # Fallback if "ingredients:" is missed
        ingredient_part = cleaned_text
        
    ingredients = [
        item.strip() 
        for item in re.split(r'[;.,]', ingredient_part) 
        if item.strip()
    ]
    return ingredients

def perform_allergy_and_score_analysis(ingredients_list, user_allergies):
    """Analyzes ingredients against user allergies and calculates a simple score."""
    detected_allergens = set()
    user_allergies_lower = {remove_diacritics(a.lower()) for a in user_allergies}
    score = 0

    for ingredient in ingredients_list:
        ingredient_lower = remove_diacritics(ingredient.lower())
        
        # Check against common and user-specific allergens
        for allergen in OFF_COMMON_ALLERGENS + list(user_allergies_lower):
            if allergen in ingredient_lower:
                detected_allergens.add(allergen.capitalize())
        
        # Scoring Check
        for bad in BAD_INGREDIENTS:
            if bad in ingredient_lower:
                score -= 5
                
        if "whole grain" in ingredient_lower or "fiber" in ingredient_lower or "protein" in ingredient_lower:
            score += 3
            
    # Convert score to a grade
    if score >= 5: score_grade = "A (Excellent)"
    elif score >= 0: score_grade = "B (Good)"
    elif score >= -5: score_grade = "C (Fair)"
    else: score_grade = "D (Poor)"
    
    return list(detected_allergens), score_grade


# --- 2. GUI APPLICATION CLASS ---
class NutriScanApp(cTk.CTk):
    
    def __init__(self):
        super().__init__()
        
        # Initialize EasyOCR Reader (Time-consuming operation, done only once)
        self.ocr_reader = self._initialize_easyocr_reader()
        
        # Configure window
        self.title("Nutri-Label App")
        self.geometry(f"{1000}x{700}")
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.user_allergies = []
        self.image_path = None
        
        cTk.set_appearance_mode("System")
        cTk.set_default_color_theme("green")

        self.create_widgets()

    def _initialize_easyocr_reader(self):
        # return
        """Initializes the EasyOCR reader with specified languages."""
        try:
            reader = easyocr.Reader(EASYOCR_LANGUAGES)
            print("EasyOCR Reader initialized successfully.")
            return reader
        except Exception as e:
            print(f"Error initializing EasyOCR: {e}")
            return None
    
    def get_text_from_image(self, image_path):
        """Uses EasyOCR to extract text from an image."""
        if not self.ocr_reader:
            return "OCR Error: EasyOCR Reader failed to initialize."
        
        try:
            # Read the image using the EasyOCR reader instance
            results = self.ocr_reader.readtext(image_path, detail=0)
            
            # Join all recognized text lines into a single string
            text = ' '.join(results)
            return text.strip()
        except Exception as e:
            return f"OCR Error during reading: {e}"


    def create_widgets(self):        
        self.header_frame = cTk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.header_frame.grid_columnconfigure((0, 1), weight=1)

        self.title_label = cTk.CTkLabel(
            self.header_frame, 
            text = "📜 Nutri-Label", 
            font = cTk.CTkFont(size=36, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=10, sticky = 'e')
        
        # --- User Input / Setup Frame ---
        self.setup_frame = cTk.CTkFrame(self)
        self.setup_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        self.setup_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Allergy Input
        self.allergy_label = cTk.CTkLabel(self.setup_frame, text="Allergies (comma separated):")
        self.allergy_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        

        ## Load possible saved allergies from file
        ## First check if file exists
        if not os.path.isfile(SAVEFILE_PATH):
            open(SAVEFILE_PATH, 'x')

        stored_allergies = ""
        with open(SAVEFILE_PATH, 'r') as f:
            stored_allergies = f.read().strip()
        allergies_var = cTk.StringVar(value=stored_allergies) if stored_allergies else None

        self.allergy_entry = cTk.CTkEntry(self.setup_frame, textvariable = allergies_var, placeholder_text="e.g., peanuts, milk, soy")
        self.allergy_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.save_button = cTk.CTkButton(self.setup_frame, text="Save Allergies", command=self.save_allergies)
        self.save_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        # --- Main Workspace Frame ---
        self.main_frame = cTk.CTkFrame(self)
        self.main_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1) 
        self.main_frame.grid_columnconfigure(1, weight=1) 
        self.main_frame.grid_rowconfigure(0, weight=1) 

        # Left Panel (Image and Controls)
        self.image_frame = cTk.CTkFrame(self.main_frame)
        self.image_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.image_frame.grid_rowconfigure(1, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)

        self.load_button = cTk.CTkButton(self.image_frame, text="📷 Load Label Image (JPG/PNG)", command=self.load_image)
        self.load_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.image_display = cTk.CTkLabel(self.image_frame, text="Image Preview Area", width=450, height=450, fg_color=("gray70", "gray20"))
        self.image_display.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.analyze_button = cTk.CTkButton(self.image_frame, text="🔬 Run Analysis", command=self.run_analysis, fg_color="darkgreen", hover_color="#005500")
        self.analyze_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # Right Panel (Results)
        self.result_frame = cTk.CTkFrame(self.main_frame)
        self.result_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.result_frame.grid_rowconfigure(3, weight=1)

        self.score_label = cTk.CTkLabel(self.result_frame, text="Nutritional Score: N/A", 
                                                  font=cTk.CTkFont(size=24, weight="bold"))
        self.score_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        self.allergy_label = cTk.CTkLabel(self.result_frame, text="Allergy Status: Ready", 
                                                    font=cTk.CTkFont(size=16), text_color="green")
        self.allergy_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        self.raw_label = cTk.CTkLabel(self.result_frame, text="Raw OCR Text:", font=cTk.CTkFont(size=14, weight="bold"))
        self.raw_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")

        self.raw_text_box = cTk.CTkTextbox(self.result_frame, height=400)
        self.raw_text_box.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")

        # Finally, load allergies if existent
        if allergies_var:
            self.save_allergies(to_file = False)


    def save_allergies(self, to_file = True):
        """Saves user allergies from the entry field."""
        raw_text = self.allergy_entry.get()
        self.user_allergies = [
            remove_diacritics(a.strip()) 
            for a in raw_text.split(',') if a.strip()
        ]
        
        if self.user_allergies:
            self.save_button.configure(text=f"Saved ({len(self.user_allergies)})", fg_color="green")
            self.allergy_label.configure(text=f"Allergy Status: {', '.join(self.user_allergies).capitalize()}", text_color="orange")
        else:
            self.save_button.configure(text="Save Allergies", fg_color="darkgreen")
            self.allergy_label.configure(text="Allergy Status: None Set", text_color="green")
        
        ## Also consider saving data to file
        if to_file:
            with open(SAVEFILE_PATH, 'w') as f:
                f.write(', '.join(self.user_allergies))

    def load_image(self):
        """Opens a file dialog and displays the selected image."""
        filepath = tkinter.filedialog.askopenfilename(
            title="Select Ingredient Label Image",
            filetypes=(("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*"))
        )
        
        if filepath:
            self.image_path = filepath
            
            # Display image in the GUI
            original_img = Image.open(self.image_path)

            image_aspect_ratio = original_img.width / original_img.height  
            max_ratio_bound = 1.75
            # Image can maybe be rescaled into a 1:1 box
            target_width, target_height = 425, 425
            ideal_width, ideal_height = 300, 300
            
            self.img_ctk = cTk.CTkImage(
                light_image = original_img,
                dark_image = original_img,
                size = (
                    target_width if image_aspect_ratio <= max_ratio_bound else original_img.width * ideal_height // original_img.height, 
                    target_height if image_aspect_ratio <= max_ratio_bound else original_img.height * ideal_width // original_img.width
                )
            )
            self.image_display.configure(image = self.img_ctk, text = '')
            self.image_display.image = self.img_ctk ## Keeps a reference to avoid garbage collection (cred)
            
            # Reset results display
            self.score_label.configure(text="Nutritional Score: Ready to Scan")
            self.allergy_label.configure(text="Allergy Status: Ready to Scan", text_color="green")
            self.raw_text_box.delete("1.0", "end")


    def run_analysis(self):
        """Performs OCR and analysis on the loaded image."""
        if not self.image_path:
            self.score_label.configure(text="ERROR: Please Load an Image First", text_color="red")
            return
        
        if not self.ocr_reader:
            self.score_label.configure(text="CRITICAL ERROR: OCR Not Initialized", text_color="red")
            return

        self.score_label.configure(text="Analyzing...", text_color="gray")
        
        # 1. OCR using EasyOCR method
        raw_ocr_text = self.get_text_from_image(self.image_path)
        
        self.raw_text_box.delete("1.0", "end")
        self.raw_text_box.insert("1.0", raw_ocr_text)

        if "OCR Error" in raw_ocr_text:
             self.score_label.configure(text=raw_ocr_text, text_color="red")
             return

        # 2. Parsing and Analysis
        ingredients = parse_ingredients(raw_ocr_text)
        allergens, score_grade = perform_allergy_and_score_analysis(ingredients, self.user_allergies)
        
        # 3. Update Results GUI
        self.score_label.configure(text=f"Nutritional Score: {score_grade}")
        
        if "A" in score_grade:
            self.score_label.configure(text_color="green")
        elif "D" in score_grade:
            self.score_label.configure(text_color="red")
        else:
            self.score_label.configure(text_color="orange")

        if allergens:
            allergy_msg = f"🚫 WARNING! Contains: {', '.join(allergens)}"
            self.allergy_label.configure(text=allergy_msg, text_color="red")
        else:
            self.allergy_label.configure(text="✅ All Clear: No Allergens Detected", text_color="green")
            

if __name__ == "__main__":
    app = NutriScanApp()
    app.mainloop()