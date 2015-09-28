-- Table: versions.version_tags

DROP TABLE versions.version_tags;

CREATE TABLE versions.version_tags
(
  tag_id serial NOT NULL,
  tag_name character varying,
  version_table_id integer,
  revision integer NOT NULL,
  CONSTRAINT version_tags_pkey PRIMARY KEY (revision),
  CONSTRAINT version_table_id_fkey FOREIGN KEY (version_table_id)
      REFERENCES versions.version_tables (version_table_id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE versions.version_tags OWNER TO barpadue;

-- Index: versions.fki_version_table_id_fkey

-- DROP INDEX versions.fki_version_table_id_fkey;

CREATE INDEX fki_version_table_id_fkey
  ON versions.version_tags
  USING btree
  (version_table_id);
