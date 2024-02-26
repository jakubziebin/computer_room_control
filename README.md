# Computer Room Control

![image](https://github.com/jakubziebin/computer_room_control/assets/116113682/583caf34-c250-4405-8bed-9e3f17a5a3f9)

Python scripts designed to monitor and manage the indoor air quality of a computer room at the University. This project utilizes a Raspberry Pi for implementation and includes a textual application for user interaction.

## How to Use

1. **Clone the Repository**: Begin by creating a virtual environment (venv) and cloning the repository using the `--recurse-submodules` flag to ensure all dependencies are included.

    ```bash
    git clone --recurse-submodules <link_to_repository>
    ```

2. **Install DHT Library**: Navigate to the `Adafruit_Python_DHT` directory and install the DHT library using the following command:

    ```bash
    cd Adafruit_Python_DHT
    sudo python3 setup.py install
    ```

3. **Install Application Dependencies**: Install the necessary dependencies by running the following command:

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the Application**: Execute the Python scripts to start monitoring and controlling the indoor air quality of the computer room.
       ```
   python app.py
       ```
