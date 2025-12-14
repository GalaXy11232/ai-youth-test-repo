# Nutri-Label

Nutri-Label is a Python application that utilizes Optical Character Recognition (OCR) libraries to check and scan pictures of different product labels for any user-inputted allergens. It also calculates a nutritional score based on the found ingredients.

## Installation

- Make sure you have python installed (preferably version python `3.11.x`)
- Download this repository's contents and extract them to a folder
- Open command prompt terminal into said folder (make sure the current directory is the same as the extracted one)
- Create a new **virtual environment** for the project (type the following into command prompt):
```bash
python -m venv .venv
```

- Activate tne virtual environment
```bash
.venv\scripts\activate
```

- Install the required modules for the program
```bash
python -m pip install -r requirements.txt
```

- You can now **run** the script freely, either by opening the `main.py` file or by typing the following (in the same command prompt):
```bash
python main.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT License](https://choosealicense.com/licenses/mit/)