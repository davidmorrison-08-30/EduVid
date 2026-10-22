## AVAILABLE COLORS AND HOW TO PRESENT THEM

🎨 Predefined Global Color Constants

The standard built-in color constants available natively in ManimGL include:

| Base Color Family | Main Constant | Gradient / Shade Sub-Constants |
| :--- | :--- | :--- |
| **Red** | `RED` | `RED_A`, `RED_B`, `RED_C`, `RED_D`, `RED_E` |
| **Blue** | `BLUE` | `BLUE_A`, `BLUE_B`, `BLUE_C`, `BLUE_D`, `BLUE_E` |
| **Green** | `GREEN` | `GREEN_A`, `GREEN_B`, `GREEN_C`, `GREEN_D`, `GREEN_E` |
| **Yellow** | `YELLOW`, `GOLD` | `YELLOW_A`, `YELLOW_B`, `YELLOW_C`, `YELLOW_D`, `YELLOW_E` |
| **Teal** | `TEAL` | `TEAL_A`, `TEAL_B`, `TEAL_C`, `TEAL_D`, `TEAL_E` |
| **Purple** | `PURPLE` | `PURPLE_A`, `PURPLE_B`, `PURPLE_C`, `PURPLE_D`, `PURPLE_E` |
| **Maroon** | `MAROON` | `MAROON_A`, `MAROON_B`, `MAROON_C`, `MAROON_D`, `MAROON_E` |
| **Grayscale & Basics** | `WHITE`, `BLACK` | `LIGHT_GRAY`, `LIGHT_GREY`, `GRAY`, `GREY`, `DARK_GRAY`, `DARK_GREY` |

(Note: In ManimGL, the main constant like GREEN is an alias mapping to GREEN_C. _A represents the lightest shade and _E represents the darkest shade).

⚡ Pure Colors

For absolute primary or secondary colors without specific aesthetic tuning, you can use:
• PURE_RED, PURE_GREEN, PURE_BLUE
• PURE_CYAN, PURE_MAGENTA, PURE_YELLOW

⚙️ Using Custom Colors

If you want to use a color outside the default palette, you pass it as a string hex value or numerical layout: 
```python
# Hex format
circle = Circle(color="#7A20A6")

# Custom RGBA mappings are also accepted dynamically
square = Square(color=[1.0, 0.5, 0.0]) 
```

## IMPORTANT RULES
Unless speicifed as a RGBA mapping list (e.g.`[1.0, 0.5, 0.0]`), the value of `color` must be a Python string i.e. enclosed in single or double quotes ('' or "")