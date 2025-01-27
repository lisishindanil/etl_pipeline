WITH domain_counts AS (
    SELECT
        domain,
        COUNT(*) AS domain_count
    FROM
        users
    GROUP BY
        domain
),
max_domain AS (
    SELECT
        domain
    FROM
        domain_counts
    WHERE
        domain_count = (SELECT MAX(domain_count) FROM domain_counts)
)
SELECT
    u.user_id,
    u.name,
    u.email,
    u.signup_date,
    u.domain
FROM
    users u
JOIN
    max_domain md ON u.domain = md.domain
ORDER BY
    u.user_id;
