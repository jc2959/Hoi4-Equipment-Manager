from database import dbinterface


if __name__ == "__main__":
    dbinterface.establish_database({"testtb": {"param1": "int", "param2": "text"}})
