sample 1

/tf-msgraph-review resource "msgraph_resource" "authenticationeventsflows_new_password" {
  url = "identity/AuthenticationEventsFlows"
  api_version = "beta"
  body = {
    displayName                     = "NEW_PASSWORD"
    description                     = null
    priority                        = 500
    onAttributeCollectionStart      = null
    onAttributeCollectionSubmit     = null
    conditions                      = {
      applications = {
        includeAllApplications = false
        includeApplications    = [
          
        ]
      }
    }
    onInteractiveAuthFlowStart      = {
      isSignUpAllowed = true
    }
    onAuthenticationMethodLoadStart = {
      identityProviders = [
        {
          id                   = "EmailPassword-OAUTH"
          displayName          = "Email with password"
          supportedTenantTypes = "externalId"
          identityProviderType = "EmailPassword"
          state                = null
        },
      ]
    }
    onAttributeCollection           = {
      accessPackages          = []
      attributeCollectionPage = {
        customStringsFileId = null
        views               = [
          {
            title       = null
            description = null
            inputs      = [
              {
                attribute        = "email"
                label            = "Email Address"
                inputType        = "text"
                defaultValue     = null
                hidden           = true
                editable         = false
                writeToDirectory = true
                required         = true
                validationRegEx  = "^[a-zA-Z0-9.!#$%&amp;&#8217;'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\\.[a-zA-Z0-9-]+)*$"
                options          = []
              },
              {
                attribute        = "displayName"
                label            = "Display Name"
                inputType        = "text"
                defaultValue     = null
                hidden           = false
                editable         = true
                writeToDirectory = true
                required         = false
                validationRegEx  = "^.*"
                options          = []
              },
            ]
          },
        ]
      }
      attributes              = [
        {
          id                    = "email"
          displayName           = "Email Address"
          description           = "Email address of the user"
          userFlowAttributeType = "builtIn"
          dataType              = "string"
          supportedTenantTypes  = "externalId"
        },
        {
          id                    = "displayName"
          displayName           = "Display Name"
          description           = "Display Name of the User."
          userFlowAttributeType = "builtIn"
          dataType              = "string"
          supportedTenantTypes  = "externalId"
        },
      ]
    }
    onUserCreateStart               = {
      userTypeToCreate = "member"
      accessPackages   = []
    }
  }
}