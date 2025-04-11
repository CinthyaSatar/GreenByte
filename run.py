from greenbyte import createApp

app = createApp()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8006, help='Port to run the server on')
    args = parser.parse_args()
    app.run(debug=True, host="0.0.0.0", port=args.port)