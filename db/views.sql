CREATE VIEW get_fulltext_with_classifications AS
SELECT d.doclang_id,
       d.crawl_id,
       d.fulltext_id,
       jsonb_object_agg(p.nr - 1, jsonb_build_object('text', p.txt, 'tokens',
                                                     (d.paralang::jsonb -> ((p.nr - 1)::text)) ->> 'tokens'::text,
                                                     'lang', (d.paralang::jsonb -> ((p.nr - 1)::text)) ->>
                                                             'lang'::text)) AS paragraphs
FROM doclangs d
         JOIN fulltext f ON f.fulltext_id = d.fulltext_id
         CROSS JOIN LATERAL ( SELECT t.nr,
                                     t.txt
                              FROM unnest(string_to_array(f.fulltext, '
'::text)) WITH ORDINALITY t(txt, nr)) p
WHERE d.paralang::jsonb ? ((p.nr - 1)::text)
GROUP BY d.doclang_id, d.crawl_id, d.fulltext_id;

CREATE VIEW get_docs AS
SELECT de.domain_entity_id, p.pathid, p.crawl_id, contenttype, p.path, ft.hash,
    sum(CASE WHEN lang.lang='nob' THEN tokens ELSE 0 END) as nob,
    sum(CASE WHEN lang.lang='nno' THEN tokens ELSE 0 END) as nno,
    sum(CASE WHEN lang.lang='eng' THEN tokens ELSE 0 END) as eng,
    sum(CASE WHEN lang.lang NOT IN ('nno', 'nob', 'eng') THEN tokens ELSE 0 END) as andre,
    CASE WHEN bpe.pathid is null THEN false ELSE true END as blokkert
FROM domain_entity de
LEFT JOIN paths p ON p.domainid = de.domainid
LEFT JOIN blocked_paths_entity bpe ON bpe.pathid = p.pathid
LEFT JOIN fulltext ft ON ft.fulltext_id = p.fulltext_id
LEFT JOIN doclangs_para lang ON lang.fulltext_id = p.fulltext_id
GROUP BY de.domain_entity_id, p.pathid, p.crawl_id, p.contenttype, p.path, ft.hash, bpe.pathid;

create view show_domain_entity_relations as
select de.domain_entity_id, d."domain", e."entityName"  from domain_entity de 
join domains d on d.domainid = de.domainid 
join entities e on e."entityID" = de.entityid;