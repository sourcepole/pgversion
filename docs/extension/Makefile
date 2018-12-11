EXTENSION = pgversion        # the extensions name
DATA = pgversion--2.0.0.sql  # script files to install

# postgres build stuff
PG_CONFIG = pg_config
PGXS := $(shell $(PG_CONFIG) --pgxs)
include $(PGXS)

