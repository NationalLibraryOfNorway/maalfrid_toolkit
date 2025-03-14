CREATE INDEX warcinfo_content_hash ON warcinfo(content_hash);
CREATE INDEX warcinfo_response_status ON warcinfo(response_status);
CREATE INDEX warcinfo_fulltext_id ON warcinfo(fulltext_id);
CREATE INDEX _wfc_ ON warcinfo(warc_file_id, response_mime_type);
CREATE INDEX doclangs_fulltext_id ON doclangs(fulltext_id);

CREATE INDEX paths_contenttype ON paths(contenttype);
--CREATE INDEX paths_warc_file_id ON paths(warc_file_id);
CREATE INDEX paths_path ON paths(path);

CREATE INDEX doclangs_para_fulltext_id ON doclangs_para(fulltext_id);
CREATE INDEX _paths_domainid_pathid_ ON paths(domainid, pathid);
