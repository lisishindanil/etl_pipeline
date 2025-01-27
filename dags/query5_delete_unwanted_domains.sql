DELETE FROM
    users
WHERE
    domain NOT IN ('gmail.com', 'yahoo.com', 'example.com');
