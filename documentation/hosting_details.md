# Hosting Details
The SE-US MBON runs the MBON-Dashboard-Server application on Google Cloud Platform.
As of 2025, all supported regional dashboards are being integrated into a single instance under the branch `unify-subdomain`.
For the ~4 client organizations the following configuration is being used:

* E2-standard-16 instance
* region US-east1 (South Carolina)

-------------------------------

# Old Documentation
Below is old documentation that should probably be ignored.
Someone should come back around and clean this up.

## Create Server on DigitalOcean

Created droplet at https://digitalocean.com with ben@ecoquants.com (Google login):

- Choose an image : Distributions : Marketplace :
  - **Docker** by DigitalOcean VERSION 18.06.1 OS Ubuntu 18.04
- Choose a plan : Standard :
  - _iea-demo.us_:
    - **$20 /mo** $0.030 /hour
    - 4 GB / 2 CPUs
    - 80 GB SSD disk
    - 4 TB transfer
  - _iea-demo.us_:
    - **$40 /mo** $0.060 /hour
    - 8 GB / 4 CPUs
    - 160 GB SSD disk
    - 5 TB transfer
- Choose a datacenter region :
  - **San Francisco** (New York currently experiencing issues)
- Authentication :
  - **One-time password**
    Emails a one-time root password to you (less secure)
- How many Droplets?
  - **1  Droplet**
- Choose a hostname :
  - _iea-demo.us_:
    - **iea-demo.us**

[DigitalOcean - iea-ne.us project](https://cloud.digitalocean.com/projects/367d3107-1892-46a8-ba53-2f10b9ba1e2d/resources?i=c03c66)


Email recieved with IP and temporary password:

- _iea-demo.us_:

  > Your new Droplet is all set to go! You can access it using the following credentials:
  >
  > Droplet Name: docker-iea-demo.us
  > IP Address: 157.245.189.38
  > Username: root
  > Password: 513dbca94734429761db936640

Have to reset password upon first login.

Saved on my Mac to a local file:

```bash
ssh root@157.245.189.38
# enter password from above
# you will be asked to change it upon login
```

```bash
echo S3cr!tpw > ~/private/password_docker-iea-ne.us
cat ~/private/password_docker-iea-ne.us
```



## Setup domain iea-ne.us

- Bought domain **iea-demo.us** for **$12/yr** with account bdbest@gmail.com.

- DNS matched to server IP `64.225.118.240` to domain **iea-demo.us** via [Google Domains]( https://domains.google.com/m/registrar/iea-ne.us/dns), plus the following subdomains added under **Custom resource records** with:

- Type: **A**, Data:**157.245.189.38** and Name:
  - **@**
  - **wp**
  - **gs**
  - **rstudio**
  - **shiny**
  - **info**
  - **erddap**
  - **ckan**
- Name: **www**, Type: **CNAME**, Data:**iea-ne.us**
