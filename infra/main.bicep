param location string = 'eastasia'
param course string = 'itcs355'
param lab string = '5'
var purposes = ['training', 'serving', 'ci']
resource identities 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = [for purpose in purposes: {
  name: 'lab5-${purpose}'
  location: location
  tags: { course: course, lab: lab }
}]
output identityIds array = [for (purpose, i) in purposes: identities[i].id]
