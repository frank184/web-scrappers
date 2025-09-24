
JOB_POSTS_QUERY = """
{
    job_posts[] {
        org_name
        job_title
        salary
        location
        contract_type(Contract or Full time)
        location_type(remote or on-site or hybrid)
        date_posted
        url
    }
}
"""