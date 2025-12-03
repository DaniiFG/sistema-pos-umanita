from app import create_app

app = create_app()

if __name__ == '__main__':
    # host='0.0.0.0' permite que otros dispositivos en la red accedan
    app.run(debug=True, port=5000, host='0.0.0.0')