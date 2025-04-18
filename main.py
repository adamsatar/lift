
import os
from user_models import create_all_user_tables
from system_models import create_all_system_tables
from sqlalchemy import create_engine

from seed import seed_all

system_engine = create_engine("sqlite:///system.db", echo=True)
user_engine = create_engine("sqlite:///user_log.db", echo=True)



if __name__ == "__main__":
    try:
        os.remove("user_log.db")
    except FileNotFoundError:
        pass  # or log it if needed

    try:
        os.remove("system.db")
    except FileNotFoundError:
        pass  # or log it if needed

    create_all_system_tables(system_engine)
    create_all_user_tables(user_engine)

    seed_all(system_engine=system_engine,user_engine=user_engine)
    print()