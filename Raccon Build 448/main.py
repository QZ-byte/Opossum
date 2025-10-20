from ui.main_ui import RacconApp

if __name__ == "__main__":
    app = RacconApp(db_path="raccon.db")
    app.run()
