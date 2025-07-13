Decentralized Online Marketplace Protocol (DOMP): Enabling Trustless Marketplaces



Table of Contents

Abstract

Introduction

Background

Bitcoin and the Lightning Network

Nostr Protocol

Anti-Spam Measures

Defined Event Types

Comprehensive Transaction Workflow

Escrow Mechanism in DOMP

Overview

Detailed Process with Code Examples

Reputation System

Storage and Reference

Reputation Calculation

Arbitration

Scenarios Demonstrating Potential Exchanges

Scenario 1: Successful Transaction

Scenario 2: Buyer Does Not Confirm Receipt

Scenario 3: Seller Fails to Ship the Item

Scenario 4: Arbitration for Dispute Resolution

Potential Attack Vectors

Conclusion



Abstract

The Decentralized Online Marketplace Protocol (DOMP) introduces a framework for secure, trustless, and transparent transactions within decentralized online marketplaces. Leveraging Bitcoin's robustness, the Lightning Network's efficiency, and the Nostr protocol's flexibility, DOMP eliminates intermediaries and enhances user trust through innovative mechanisms such as a dual-collateral system, a reputation framework, and an optional arbitration process. By defining specific event types to structure interactions, DOMP ensures secure fund management and mitigates fraud risks inherent in decentralized commerce.

Unlike existing protocols, DOMP uniquely addresses challenges of trust and security without relying on third-party escrow services. It employs a combination of cryptographic proofs and mutual agreements to establish an escrow mechanism at the protocol level. Additionally, DOMP implements market-driven anti-spam measures, allowing relays to set their own policies based on network conditions, thereby enhancing resilience and adaptability.

By detailing transaction workflows, escrow mechanisms, reputation systems, and mitigation strategies against potential attack vectors, DOMP aims to provide a comprehensive solution for peer-to-peer commerce. It advances the vision of a decentralized marketplace where participants can transact with some amount of confidence and free from censorship.



Background

Bitcoin and the Lightning Network

Bitcoin, introduced in 2009, is a decentralized digital currency that enables peer-to-peer transactions without the need for a central authority or intermediary. Its blockchain technology ensures transparency, security, and immutability of transactions. However, Bitcoin's scalability limitations and transaction fees present challenges for high-frequency or microtransaction-based applications, such as online marketplaces.

The Lightning Network (LN) addresses these challenges by introducing an off-chain payment protocol that allows for near-instantaneous and low-fee transactions. By establishing bi-directional payment channels between users, LN enables multiple transactions to occur off the main blockchain, reducing congestion and fees. This scalability solution makes LN particularly well-suited for handling the microtransactions allowing for more flexible client integrations in the future like the possibility of streaming data, CPU cycles, and more.

The Nostr Protocol

Nostr (Notes and Other Stuff Transmitted by Relays) is a decentralized, open-source protocol designed for creating and propagating events across a distributed network of relays. Unlike traditional centralized platforms, Nostr operates without central servers, relying instead on a network of relays that store and forward messages. Users publish and subscribe to events using public and private key cryptography, ensuring data integrity and user privacy.

Nostr's resilience against censorship and its flexible, event-driven architecture make it an ideal choice for DOMP's communication layer. By utilizing Nostr, DOMP facilitates direct interactions between marketplace participants without reliance on centralized infrastructure. As of 2024, Nostr has gained significant traction within the decentralized application community, with growing adoption due to its simplicity and effectiveness in enabling decentralized social networks and communication platforms. Its compatibility with DOMP ensures that the protocol can leverage existing Nostr infrastructure while contributing to its ecosystem.

Anti-Spam Measures

In decentralized networks, spam and malicious activities can degrade user experience and network performance. To maintain network integrity and prevent abuse, DOMP incorporates a combination of anti-spam measures. 

Lightning Network (LN) Payments:

DOMP Clients (or individual Nostr Relays) may require small LN payments to incentivize relays for handling and retaining specific events. This economic disincentive increases the cost of spamming, making it financially unattractive for attackers. Users can also rate relays (see section: reputation system) based on reliability, creating a market-driven ecosystem where high-quality relays are rewarded accordingly.

Proof of Work (PoW) via NIP13:

DOMP Clienst (or individual Nostr Relays) may utilize PoW as an alternative, or in addition to, to LN payments, allowing users to perform computational challenges as a resource-based proof. This method is akin to mechanisms used in systems like Hashcash to prevent spam and denial-of-service attacks. Using the Nostr NIP13 standard, DOMP ensures compatibility with existing Nostr implementations. This approach provides users without access to the Bitcoin or Lightning Networks a way to participate, enhancing inclusivity.

Hashing and Event Referencing:

To prevent abuse of the reputation system, DOMP requires certain events—primarily reputation events—to include hashes of valid previous events signed by the user. This ensures that only participants involved in legitimate transactions can influence reputation scores. This method mitigates the risk of Sybil attacks, where an attacker might create multiple fake identities to manipulate the system, a common issue in decentralized protocols.

Relay-Determined Anti-Spam Policies:

Instead of enforcing a one-size-fits-all solution, DOMP allows individual relays to set their own anti-spam requirements, including PoW difficulty or LN payment amounts. This market-driven approach is similar to how email servers implement their own spam filters and policies. It enables relays to adjust their policies based on network conditions, demand, and their capacity, promoting flexibility and resilience. Users can select relays that balance strictness and accessibility according to their preferences.

Comparison with Existing Protocols:

DOMP's hybrid approach combines economic incentives and computational proofs.  DOMP's strategy enhances security and accessibility by reducing barriers to entry while effectively discouraging spam and malicious behavior. By allowing relays to set their own policies, the protocol adapts to varying network conditions and user needs.



Defined Event Types

DOMP defines specific event types to structure interactions within the marketplace. Each event includes mandatory fields such as id, pubkey, created\_at, sig, and references to previous events where applicable.

Listing and Bidding

kind-300: Product Listing: Sellers list products for sale, including details and anti-spam proof.

kind-301: Bid Submission: Buyers place bids referencing the kind-300 listing.

kind-302: Counter Bid: Used by either party to propose revised terms during negotiations. This event references a previous bid or counter bid and includes LN invoice and collateral information.

kind-303: Bid Acceptance: Indicates unconditional acceptance of the bid with the original terms.

Note on Merging kind-302 and kind-303: While combining these event types was considered, and could simplify the protocol, we've chosen to keep them separate to enhance clarity and user confidence. Having distinct event types allows users to immediately recognize whether terms have changed (kind-302) or if a bid is accepted as-is (kind-303), reducing the risk of misunderstandings.

Payments, Escrow, and Completion

kind-310: Collateral Deposit: Logs when a seller deposits collateral.

kind-311: Payment Confirmation: Buyers confirm payment, activating escrow. This event references collateral deposits from both parties for verification.

kind-312: Escrow Dispute: Initiated by either party seeking release of funds.

kind-313: Receipt Confirmation: Buyers confirm item receipt, releasing escrowed funds.

kind-314: Refund Initiation: Sellers initiate a refund if required.

kind-315: Mutual Agreement: Logs mutual consent to release funds or cancel the transaction.

kind-316: Arbitration Offer: A third-party user offers to arbitrate the dispute.

Communication and Feedback

kind-320: Communication Message: General communication between parties, such as messages, notifications, or updates. Requires PoW, LN payment, or cryptographic link.

kind-321: User Reputation Feedback: Post-transaction ratings, enhancing transparency. Must reference specific prior events to validate the feedback.

kind-322: Arbitrator Reputation Feedback: Ratings for arbitrators after dispute resolution.

kind-323: Relay Reputation Feedback: Ratings for relays based on service quality.



Comprehensive Transaction Workflow

DOMP’s workflow is designed to streamline interactions between buyers and sellers, using well-defined steps and events. Below, we include code samples for each event kind and discuss the reasoning behind certain design choices.

Step 1: Product Listing by Seller (kind-300)

Upload Product Details: Sellers provide descriptions and images using HTML links or IPFS Content Identifiers (CIDs).

Relay Selection and Compensation: Sellers choose multiple Nostr relays to publish their product listings, compensating them according to each relay's anti-spam requirements.

Event Broadcasting: Sellers broadcast the kind-300 event containing product details and anti-spam proofs.

{

&nbsp; "kind": 300,

&nbsp; "pubkey": "seller\_pubkey",

&nbsp; "created\_at": 1620000000,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "LN\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"product\_name\\": \\"Digital Camera\\", \\"description\\": \\"A high-quality DSLR camera.\\", \\"price\_satoshis\\": 80000000, \\"storage\_link\\": \\"ipfs://CID\\"}",

&nbsp; "id": "event\_id\_300",

&nbsp; "sig": "signature\_seller\_300"

}

Step 2: Seller Posts Collateral (kind-310)

Seller Posts Collateral First: To build buyer confidence and demonstrate commitment, the seller deposits their collateral before the buyer proceeds. This reduces the risk of the seller trolling and encourages serious participation.  Since the seller can refund all funds (including their own collateral) if the buyer stops participating, this poses no additional risk to the seller.

Sequence: This event would likely be done in conjunction with a kind-300 listing.  It is not necessarily required by the protocol, but may be required by application clients.  As a buyer it would be wise to make sure a seller has posted their collateral to before committing any funds to escrow to make sure the seller has “skin in the game” and cannot just freeze buyers’ funds in escrow as a way to troll online.

Collateral Amounts:  We imagine seller collateral would generally be a lot less than for buyers since the seller’s collateral is primarily just a spam and trolling control mechanism.  In my thought experiments we usually considered 10% of the purchase price sufficient, although for very large sale prices less would probably suffice, and vice versa for very small sale prices.

{

&nbsp; "kind": 310,

&nbsp; "pubkey": "seller\_pubkey",

&nbsp; "created\_at": 1620000050,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_seller\_collateral"]

&nbsp; ],

&nbsp; "content": "{\\"product\_ref\\": \\"event\_id\_300\\", \\"collateral\_amount\_satoshis\\": 8000000}",

&nbsp; "id": "event\_id\_310\_seller",

&nbsp; "sig": "signature\_seller\_310"

}

Step 3: Buyer Submits a Bid (kind-301)

Bid Discovery: Buyers find products via subscribing to kind-300 events.  Realistically this would be done through clients who specialize in these kinds of interactions, but could theoretically be done manually by a user.

Bid Submission: Buyers submit a kind-301 event referencing the product and including their proposed terms and collateral amount.

Collateral Amounts:  Typically, buyer collateral will likely be higher than than that of sellers, as it is meant to incentivizethe buyer to confirm receipt of the item and release purchas funds to the seller.

Relay Verification: Relays process the bid according to their anti-spam policies.

{

&nbsp; "kind": 301,

&nbsp; "pubkey": "buyer\_pubkey",

&nbsp; "created\_at": 1620000100,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "LN\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"product\_ref\\": \\"event\_id\_300\\", \\"bid\_amount\_satoshis\\": 80000000, \\"buyer\_contact\\": \\"buyer\_pubkey\\", \\"collateral\_amount\_satoshis\\": 80000000}",

&nbsp; "id": "event\_id\_301",

&nbsp; "sig": "signature\_buyer\_301"

}

Step 4: Seller Responds to the Bid

Option 1: Accept the Bid (kind-303)

Bid Acceptance: The seller accepts the bid without changing any terms.

Establishing Escrow: The LN invoice included in the kind-303 event is used by the buyer to make the payment. This payment, along with the buyer's collateral, is held in escrow until the transaction is completed. The escrow is established through the protocol's agreement between the buyer and seller, referencing the payment and collateral events.

{

&nbsp; "kind": 303,

&nbsp; "pubkey": "seller\_pubkey",

&nbsp; "created\_at": 1620000200,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "lnbc1invoice\_seller"]

&nbsp; ],

&nbsp; "content": "{\\"bid\_ref\\": \\"event\_id\_301\\", \\"ln\_invoice\\": \\"lnbc1invoice\_seller\\", \\"seller\_collateral\_ref\\": \\"event\_id\_310\_seller\\"}",

&nbsp; "id": "event\_id\_303",

&nbsp; "sig": "signature\_seller\_303"

}

Option 2: Propose a Counter Bid (kind-302)

Counter Bid: The seller proposes new terms, possibly adjusting the price or collateral requirements.

{

&nbsp; "kind": 302,

&nbsp; "pubkey": "seller\_pubkey",

&nbsp; "created\_at": 1620000200,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "lnbc1invoice\_seller"]

&nbsp; ],

&nbsp; "content": "{\\"bid\_ref\\": \\"event\_id\_301\\", \\"counter\_offer\_satoshis\\": 85000000, \\"ln\_invoice\\": \\"lnbc1invoice\_seller\\", \\"seller\_collateral\_ref\\": \\"event\_id\_310\_seller\\"}",

&nbsp; "id": "event\_id\_302",

&nbsp; "sig": "signature\_seller\_302"

}



Step 5: Buyer’s Response to Seller

Option 1: Accepting the Bid (kind-311)



Accepting: If the seller accepted the bid (kind-303), the buyer proceeds to deposit their collateral and confirm payment with a kind-311 event.  This would include the buyers agreed upon collateral as well as the agreed upon sale price.

Collateral Verification: Before proceeding, both parties verify that the collateral amounts match the agreed terms by referencing the kind-310 events in the kind-311 event.

Escrow Activation: The buyer's payment and both parties' collateral are now held in escrow. Either a LN HTLC or on-chain 2-of-2 multi-sig transaction can be used for escrow depending on the circumstance.



Buyer's Payment Confirmation (kind-311)

{

&nbsp; "kind": 311,

&nbsp; "pubkey": "buyer\_pubkey",

&nbsp; "created\_at": 1620000300,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_buyer\_payment"]

&nbsp; ],

&nbsp; "content": "{\\"bid\_ref\\": \\"event\_id\_303\_or\_302\\", \\"payment\_method\\": \\"htlc\\", \\"payment\_proof\\": \\"ln\_payment\_hash\_buyer\_payment\\", \\"collateral\_amount\_satoshis\\": 80000000, \\"collateral\_payment\_proof\\": \\"ln\_payment\_hash\_buyer\_collateral\\", \\"seller\_collateral\_ref\\": \\"event\_id\_310\_seller\\"}",

&nbsp; "id": "event\_id\_311",

&nbsp; "sig": "signature\_buyer\_311"

}

Option 2: Responding to a Counter Bid (kind-302)

Responding to a Counter Bid: Alternatively, the buyer can propose another counter bid (kind-302).  Repeats step 4.



Step 6: Transaction Completion and Escrow Handling

Seller Ships the Item: The seller fulfills their obligation by shipping the item.

Seller Notifies Buyer of Shipment (kind-320)

Communication: The seller uses a kind-320 event to inform the buyer that the item has been shipped, providing tracking information if available.

{

&nbsp; "kind": 320,

&nbsp; "pubkey": "seller\_pubkey",

&nbsp; "created\_at": 1620000400,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"message\\": \\"Item has been shipped. Tracking number: XYZ123\\", \\"ref\\": \\"event\_id\_311\\"}",

&nbsp; "id": "event\_id\_320\_seller",

&nbsp; "sig": "signature\_seller\_320"

}

Step 7: Receipt Confirmation (kind-313)

Buyer Confirms Receipt: Upon receiving the item, the buyer confirms receipt, triggering the release of all funds.  Collateral payments are refunded to both originators, and sale funds are released to the seller.

Automatic Release: Upon receipt confirmation, the escrowed payment and collateral are released to the seller and buyer, respectively.

No Third-Party Involvement: The release is managed by the protocol rules and enforced by the clients' software.  This is because there is no reliable way to prove receipt of a physical object at the protocol level.  Any attempt to do this would inevitably lead to potential for buyers or sellers to defraud the other party.  There is the potential for disputes by third parties, but those are largely relegated to off protocol.

{

&nbsp; "kind": 313,

&nbsp; "pubkey": "buyer\_pubkey",

&nbsp; "created\_at": 1620000800,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_buyer\_payment"]

&nbsp; ],

&nbsp; "content": "{\\"payment\_ref\\": \\"event\_id\_311\\", \\"status\\": \\"received\\"}",

&nbsp; "id": "event\_id\_313",

&nbsp; "sig": "signature\_buyer\_313"

}

Step 8: Reputation Feedback (kind-321)

Feedback Submission: Both parties submit feedback, contributing to each other's reputation scores.

Mandatory Reference to Previous Events: To prevent abuse, the kind-321 event must reference a specific previous event, and each transaction can only be referenced once in reputation events.

Requirements for kind-321:

Rating a Seller: The buyer must include a reference to a valid kind-313 (Receipt Confirmation), kind-314 (Refund Initiation), or kind-315 (Mutual Agreement) event to prove they were involved in the transaction.

Rating a Buyer: The seller must include a reference to a valid kind-313 (Receipt Confirmation), kind-314 (Refund Initiation), or kind-315 (Mutual Agreement) event.

One Feedback per Transaction: Each referenced event can only be used once for a valid kind-321 rating to prevent multiple ratings from the same transaction.

Explanation:

user\_pubkey: The public key of the user being rated.

transaction\_ref: The ID of the referenced event (e.g., kind-313).

transaction\_kind: The kind of the referenced event.

Validation: Clients must verify that the transaction\_ref corresponds to a valid event of the specified kind and that it has not been used in another kind-321 event by the same rater.

Code Sample for Rating a Seller:

{

&nbsp; "kind": 321,

&nbsp; "pubkey": "buyer\_pubkey",

&nbsp; "created\_at": 1620000900,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"user\_pubkey\\": \\"seller\_pubkey\\", \\"rating\\": 5, \\"comment\\": \\"Excellent transaction. Highly recommended.\\", \\"transaction\_ref\\": \\"event\_id\_313\\", \\"transaction\_kind\\": 313}",

&nbsp; "id": "event\_id\_321\_buyer",

&nbsp; "sig": "signature\_buyer\_321"

}

Code Sample for Rating a Buyer:

{

&nbsp; "kind": 321,

&nbsp; "pubkey": "seller\_pubkey",

&nbsp; "created\_at": 1620000950,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"user\_pubkey\\": \\"buyer\_pubkey\\", \\"rating\\": 5, \\"comment\\": \\"Prompt payment and good communication.\\", \\"transaction\_ref\\": \\"event\_id\_313\\", \\"transaction\_kind\\": 313}",

&nbsp; "id": "event\_id\_321\_seller",

&nbsp; "sig": "signature\_seller\_321"

}



Escrow Mechanism in DOMP

Overview

The escrow mechanism in DOMP is a critical component that ensures secure and trustless transactions between buyers and sellers without requiring a third-party escrow agent or relying on built-in escrow functionality within the Lightning Network (LN). Instead, DOMP implements escrow at the protocol level using cryptographic proofs, mutual agreements, and strict adherence to protocol rules enforced by client software.

Key Characteristics of the DOMP Escrow Mechanism:

Protocol-Level Implementation: Escrow is managed through DOMP's defined event types and workflow.

No Third-Party Custody: Funds are not held by a third party but are controlled by the protocol rules and cryptographic agreements between buyer and seller.

Mutual Assurance through Collateral: Both parties post collateral, incentivizing honest behavior and commitment to the transaction.

Event-Driven Control: Specific events trigger changes in the state of the escrow, such as releasing funds upon buyer confirmation.

Client Enforcement: Client software enforces the protocol rules, ensuring compliance and preventing unauthorized actions.

Detailed Process with Code Examples

Below is a step-by-step explanation of how the escrow mechanism works within DOMP, including code examples to illustrate each stage.

Step 1: Seller Lists the Product (kind-300)

Step 2: Seller Posts Collateral (kind-310)

Step 3: Buyer Submits a Bid (kind-301)

Step 4: Seller Accepts the Bid (kind-303)

Step 5: Buyer Deposits Collateral and Makes Payment

Buyer's Collateral Deposit and Payment Confirmation (kind-311)

Explanation:

The buyer confirms that the payment has been made by providing the payment\_proof (the hash of the LN payment).

The buyer\_collateral\_ref and seller\_collateral\_ref fields reference the collateral deposits made by both parties.

This event effectively locks the funds (payment and both collaterals) into the protocol's escrow mechanism.

How the Escrow Is Established:

Mutual Agreement and Protocol Enforcement:

By referencing the same bid\_ref and collateral events, both parties agree to the terms of the transaction.

The protocol rules dictate that funds are now considered in escrow and cannot be unilaterally accessed by either party.

Client Software Role:

Clients enforce the protocol by preventing users from accessing funds in escrow until the appropriate conditions are met.

They monitor the Nostr network for relevant events and update the transaction state accordingly.

Use of Cryptographic Proofs:

Payment proofs and digital signatures ensure the authenticity of transactions.

The use of event IDs and references creates an immutable chain of events that can be verified by both parties.

Step 6: Escrow Activation

Funds Held Securely: The buyer's payment and both parties' collateral are now held in escrow as per the protocol rules.

Step 7: Seller Ships the Item

The seller, assured that the funds are secured in escrow, proceeds to ship the item.

Step 8: Seller Notifies Buyer of Shipment (kind-320)

Step 9: Buyer Confirms Receipt (kind-313)

Step 10: Funds and Collateral Release

Triggered by kind-313: The buyer's receipt confirmation signals that the conditions for releasing funds are met.

Client Enforcement: Clients update the transaction state, allowing the seller to access the payment and both parties to retrieve their collateral.

No Third-Party Intervention Required: The protocol and client software handle the release based on the events recorded.

Example Code Flow for Escrow Handling

1\. Escrow Initialization:

Buyer and Seller Collateral Deposits (kind-310 and kind-311):

Both parties' collaterals are associated with the transaction through their respective kind-310 (for seller) and kind-311 (for buyer) events.

The payment\_proof in these events verifies that the collateral has been paid via LN.

Payment Confirmation (kind-311):

The buyer's payment for the item is confirmed.

References to both collateral events are included, linking all funds to the transaction.

2\. Escrow Locking Mechanism:

Protocol Rules:

Funds are considered locked once the kind-311 event is published.

Clients enforce that these funds cannot be accessed until a kind-313 (Receipt Confirmation), Kind-314 (Refund  Initiation), or kind-315 (Mutual Agreement) event occurs.

Event Chain Verification:

Each event includes references to previous events, creating a verifiable chain.

This ensures that all parties have fulfilled their obligations up to this point.

3\. Escrow Release Conditions:

Receipt Confirmation (kind-313):

Upon the buyer's confirmation, clients recognize that the transaction is complete.

Funds are released according to the protocol: the seller receives the payment, and both parties retrieve their collateral.

Alternative Release through Mutual Agreement (kind-315):

If both parties agree to cancel the transaction, they can release funds back to their original owners.

4\. Example Client-Side Enforcement Logic:

def handle\_event(event):

&nbsp;   if event.kind == 311:  # Payment Confirmation

&nbsp;       escrow = create\_escrow(event)

&nbsp;   elif event.kind == 313:  # Receipt Confirmation

&nbsp;       escrow = get\_escrow(event\['content']\['payment\_ref'])

&nbsp;       if escrow and escrow.is\_active:

&nbsp;           release\_funds(escrow)

&nbsp;   elif event.kind == 315:  # Mutual Agreement

&nbsp;       escrow = get\_escrow(event\['content']\['payment\_ref'])

&nbsp;       if escrow and escrow.is\_active and mutual\_agreement(event):

&nbsp;           refund\_funds(escrow)



def create\_escrow(event):

&nbsp;   # Verify payment and collateral proofs

&nbsp;   # Lock funds in escrow

&nbsp;   return EscrowObject(...)



def release\_funds(escrow):

&nbsp;   # Transfer payment to seller

&nbsp;   # Return collaterals to both parties

&nbsp;   escrow.is\_active = False



def refund\_funds(escrow):

&nbsp;   # Return payment and collaterals to original parties

&nbsp;   escrow.is\_active = False



def mutual\_agreement(event):

&nbsp;   # Check that both parties have agreed to the terms

&nbsp;   return True  # Simplified for illustration



5\. Security and Integrity:

Cryptographic Verification:

All events are signed by the respective parties, ensuring authenticity.

Payment proofs and references prevent fraudulent claims.

No Central Authority Needed:

The protocol and client software handle all aspects of the escrow, maintaining decentralization.

Example Playthrough Summary:

Initiation:

Seller lists item and posts collateral.

Buyer submits bid.

Agreement:

Seller accepts bid.

Buyer deposits collateral and confirms payment.

Escrow Activation:

Funds (payment and collaterals) are locked in escrow by the protocol rules.

Transaction Completion:

Seller ships item.

Buyer confirms receipt.

Funds are automatically released by client software per protocol rules.

What Happens If Disputes Arise?

Buyer Does Not Confirm Receipt:

Seller can initiate a dispute (kind-312).

Parties can communicate via kind-320 events.

They may reach a mutual agreement (kind-315) or opt for arbitration (kind-316).

Protocol Enforcement:

Funds remain in escrow until a resolution is achieved.

Collateral incentivizes both parties to resolve disputes although this can never be guaranteed in a decentralized system and some amount of trust and collaboration required between buyers and sellers will always be a limiting factor.  Buyers and sellers are allowed to establish their own risk profiles through negotiating collateral requirements within any single bid taking into account the sale item itself along with the other party’s repuation. 



Reputation System

A functioning reputation system which is very difficult to manipulate is vital to DOMP’s functioning.  It is the main way buyers and sellers can establish acceptable collateral levels for individual purchases.

Storage and Reference

Decentralized Storage: Reputation feedback events are stored on Nostr relays.

Reference by Identifier: Each reputation event references the entity being rated using appropriate identifiers (e.g., pubkey for users and arbitrators, URL for relays).

Event Types for Reputation Feedback

kind-321: User Reputation Feedback

Used for rating buyers and sellers.

Must reference specific prior transaction events to validate the feedback.

kind-322: Arbitrator Reputation Feedback

Used for rating arbitrators.

Must reference specific arbitration events (kind-316, kind-312, kind-315) to validate the feedback.

Only participants involved in the arbitration can rate the arbitrator.

kind-323: Relay Reputation Feedback

Used for rating relays.

Must include proof of interaction with the relay, such as a payment proof or service usage evidence.

Relay is identified by its URL or domain name.



Reputation Details \& Calculations

Kind 321 - User Reputation Feedback

Client Responsibilities:

Fetching Events: Clients fetch kind-321 events related to a user.

Validating Feedback: Clients verify that each kind-321 event includes a valid reference to a prior event and that it has not been used before.

Calculating Scores: Clients compute reputation scores based on valid, non-duplicated feedback.

Prevention of Abuse:

Event Validation: By requiring references to specific events, only users who participated in a transaction can provide feedback.

Single Use of References: Each transaction event can only be referenced once in reputation events to prevent multiple ratings from a single transaction.

Example User Reputation Algorithm:

def calculate\_reputation(user\_pubkey):

&nbsp;   feedback\_events = get\_feedback\_events(user\_pubkey)

&nbsp;   valid\_feedback = \[]

&nbsp;   used\_transaction\_refs = set()



&nbsp;   for event in feedback\_events:

&nbsp;       transaction\_ref = event\['content']\['transaction\_ref']

&nbsp;       transaction\_kind = event\['content']\['transaction\_kind']



&nbsp;       # Check if the transaction\_ref has already been used

&nbsp;       if transaction\_ref in used\_transaction\_refs:

&nbsp;           continue  # Skip duplicate feedback



&nbsp;       # Validate the referenced event

&nbsp;       if not validate\_transaction\_event(transaction\_ref, transaction\_kind, event\['pubkey'], user\_pubkey):

&nbsp;           continue  # Skip invalid references



&nbsp;       used\_transaction\_refs.add(transaction\_ref)

&nbsp;       valid\_feedback.append(event)



&nbsp;   # Calculate reputation score based on valid\_feedback

&nbsp;   total\_score = 0

&nbsp;   total\_weight = 0

&nbsp;   for event in valid\_feedback:

&nbsp;       rating = event\['content']\['rating']

&nbsp;       transaction\_value = get\_transaction\_value(event\['content']\['transaction\_ref'])

&nbsp;       weight = transaction\_value

&nbsp;       total\_score += rating \* weight

&nbsp;       total\_weight += weight



&nbsp;   reputation\_score = total\_score / total\_weight if total\_weight > 0 else 0

&nbsp;   return reputation\_score



def validate\_transaction\_event(transaction\_ref, transaction\_kind, rater\_pubkey, rated\_pubkey):

&nbsp;   transaction\_event = get\_event\_by\_id(transaction\_ref)

&nbsp;   if not transaction\_event:

&nbsp;       return False



&nbsp;   # Check if the transaction\_kind matches the event's kind

&nbsp;   if transaction\_event\['kind'] != transaction\_kind:

&nbsp;       return False



&nbsp;   # Verify that the rater and rated users were involved in the transaction

&nbsp;   involved\_pubkeys = {transaction\_event\['pubkey'], transaction\_event.get('counterparty\_pubkey')}

&nbsp;   if rater\_pubkey not in involved\_pubkeys or rated\_pubkey not in involved\_pubkeys:

&nbsp;       return False



&nbsp;   return True



kind-322: Arbitrator Reputation Feedback

Requirements for kind-322:

Rating an Arbitrator: The user must include a reference to a valid arbitration event, such as:

kind-316 (Arbitration Offer)

kind-312 (Escrow Dispute)

kind-315 (Mutual Agreement involving arbitration)

One Feedback per Arbitration: Each arbitration event can only be referenced once for a valid kind-322 rating.

Code Sample for Rating an Arbitrator:

{

&nbsp; "kind": 322,

&nbsp; "pubkey": "user\_pubkey",

&nbsp; "created\_at": 1620001000,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"arbitrator\_pubkey\\": \\"arbitrator\_pubkey\\", \\"rating\\": 4, \\"comment\\": \\"Fair and timely resolution.\\", \\"arbitration\_ref\\": \\"event\_id\_316\\", \\"arbitration\_kind\\": 316}",

&nbsp; "id": "event\_id\_322\_user",

&nbsp; "sig": "signature\_user\_322"

}

kind-323: Relay Reputation Feedback

Purpose: Enables users to rate relays based on their service quality.

Validation: Requires proof of interaction with the relay.

Requirements for kind-323:

Identification of Relay: Relays are identified by their URL or domain name (relay\_url).

Proof of Interaction: Users must provide evidence of interaction, such as:

Payment proof to the relay (e.g., for anti-spam measures)

Event IDs of events successfully propagated by the relay

One Feedback per Interaction: Each interaction can be referenced once for feedback.

Code Sample for Rating a Relay:

{

&nbsp; "kind": 323,

&nbsp; "pubkey": "user\_pubkey",

&nbsp; "created\_at": 1620001050,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"relay\_url\\": \\"relay1.example.com\\", \\"rating\\": 5, \\"comment\\": \\"Reliable and fast service.\\", \\"interaction\_proof\\": {\\"payment\_proof\\": \\"ln\_payment\_hash\_relay\_fee\\", \\"event\_id\\": \\"event\_id\_300\\"}}",

&nbsp; "id": "event\_id\_323\_user",

&nbsp; "sig": "signature\_user\_323"

}

Example Arbitrator and Relay Reputation Algorithm:

Note For Arbitrators:

Validation: Clients must verify that the arbitration\_ref corresponds to a valid arbitration event involving both the rater and the arbitrator.

Single Use of References: Each arbitration event can only be referenced once per rater in reputation events.

Note For Relays:

Validation: Clients verify the interaction\_proof to ensure the user interacted with the relay.

Relay Identification: Since relays do not have pubkey, they are identified by relay\_url.

def calculate\_arbitrator\_reputation(arbitrator\_pubkey):

&nbsp;   feedback\_events = get\_arbitrator\_feedback\_events(arbitrator\_pubkey)

&nbsp;   valid\_feedback = \[]

&nbsp;   used\_arbitration\_refs = set()

&nbsp;   

&nbsp;   for event in feedback\_events:

&nbsp;       arbitration\_ref = event\['content']\['arbitration\_ref']

&nbsp;       arbitration\_kind = event\['content']\['arbitration\_kind']

&nbsp;       

&nbsp;       if arbitration\_ref in used\_arbitration\_refs:

&nbsp;           continue  # Skip duplicate feedback

&nbsp;       

&nbsp;       if not validate\_arbitration\_event(arbitration\_ref, arbitration\_kind, event\['pubkey'], arbitrator\_pubkey):

&nbsp;           continue  # Skip invalid references

&nbsp;       

&nbsp;       used\_arbitration\_refs.add(arbitration\_ref)

&nbsp;       valid\_feedback.append(event)

&nbsp;   

&nbsp;   # Calculate reputation score based on valid\_feedback (similar to user reputation)

&nbsp;   # ...



def calculate\_relay\_reputation(relay\_url):

&nbsp;   feedback\_events = get\_relay\_feedback\_events(relay\_url)

&nbsp;   valid\_feedback = \[]

&nbsp;   used\_interaction\_proofs = set()

&nbsp;   

&nbsp;   for event in feedback\_events:

&nbsp;       interaction\_proof = event\['content']\['interaction\_proof']

&nbsp;       proof\_id = hash(interaction\_proof)  # Create a unique identifier for the proof

&nbsp;       

&nbsp;       if proof\_id in used\_interaction\_proofs:

&nbsp;           continue  # Skip duplicate feedback

&nbsp;       

&nbsp;       if not validate\_interaction\_proof(interaction\_proof, event\['pubkey'], relay\_url):

&nbsp;           continue  # Skip invalid proofs

&nbsp;       

&nbsp;       used\_interaction\_proofs.add(proof\_id)

&nbsp;       valid\_feedback.append(event)

&nbsp;   

&nbsp;   # Calculate reputation score based on valid\_feedback (e.g., average rating)

Arbitration

Step 1: Dispute Arises

A dispute may occur due to issues such as:

Non-receipt of Goods: The buyer claims the item was not delivered.

Goods Not as Described: The buyer asserts that the received item differs significantly from the description.

Payment Issues: The seller alleges that payment was not received or was incorrect.

Either party can initiate the arbitration process to seek a fair resolution.

Step 2: Initiation of Dispute (kind-312)

The party initiating the dispute publishes a kind-312 event to signal the existence of a dispute.

{

&nbsp; "kind": 312,

&nbsp; "pubkey": "buyer\_pubkey",

&nbsp; "created\_at": 1620000850,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"payment\_ref\\": \\"event\_id\_311\\", \\"reason\\": \\"Item not received\\", \\"details\\": \\"Expected delivery date has passed without receipt.\\"}",

&nbsp; "id": "event\_id\_312",

&nbsp; "sig": "signature\_buyer\_312"

}



Step 3: Selection of Arbitrator

Option 1: Arbitrator Offers Services (kind-316)

Arbitrators monitor the network for dispute events and can offer their services by publishing kind-316 events.

{

&nbsp; "kind": 316,

&nbsp; "pubkey": "arbitrator\_pubkey",

&nbsp; "created\_at": 1620000900,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"dispute\_ref\\": \\"event\_id\_312\\", \\"arbitrator\_pubkey\\": \\"arbitrator\_pubkey\\", \\"terms\\": \\"Arbitration fee of 2% of transaction value, payable upon resolution.\\", \\"fee\_satoshis\\": 1600000, \\"contact\_info\\": \\"arbitrator@example.com\\"}",

&nbsp; "id": "event\_id\_316",

&nbsp; "sig": "signature\_arbitrator\_316"

}



Arbitrator Fee: The arbitrator specifies their fee in satoshis or as a percentage of the transaction value.

Terms and Conditions: The arbitrator outlines their terms, including how the fee is to be paid and any additional conditions.

Option 2: Parties Select Arbitrator Directly

Alternatively, the disputing parties may choose an arbitrator they trust, perhaps based on prior interactions or reputation scores.

Step 4: Agreement to Arbitrate and Release of Funds (kind-315)

Both parties must agree to arbitration by publishing kind-315 events. Upon mutual agreement, the protocol releases the disputed funds and both parties' collateral to the arbitrator.

Buyer Agrees to Arbitration:

{

&nbsp; "kind": 315,

&nbsp; "pubkey": "buyer\_pubkey",

&nbsp; "created\_at": 1620000950,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"payment\_ref\\": \\"event\_id\_311\\", \\"agreement\\": \\"Agree to arbitration by arbitrator\_pubkey\\", \\"arbitrator\_ref\\": \\"event\_id\_316\\", \\"release\_funds\_to\_arbitrator\\": true}",

&nbsp; "id": "event\_id\_315\_buyer",

&nbsp; "sig": "signature\_buyer\_315"

}

Seller Agrees to Arbitration:

{

&nbsp; "kind": 315,

&nbsp; "pubkey": "seller\_pubkey",

&nbsp; "created\_at": 1620000960,

&nbsp; "tags": \[

&nbsp;   \["anti\_spam\_proof", "ln\_payment\_hash\_or\_PoW\_proof"]

&nbsp; ],

&nbsp; "content": "{\\"payment\_ref\\": \\"event\_id\_311\\", \\"agreement\\": \\"Agree to arbitration by arbitrator\_pubkey\\", \\"arbitrator\_ref\\": \\"event\_id\_316\\", \\"release\_funds\_to\_arbitrator\\": true}",

&nbsp; "id": "event\_id\_315\_seller",

&nbsp; "sig": "signature\_seller\_315"

}

Release of Funds: The release\_funds\_to\_arbitrator flag indicates that both parties consent to transfer the funds to the arbitrator.

Step 5: Transfer of Funds to Arbitrator

Upon mutual agreement:

Protocol Action: The protocol, via client software compliance, facilitates the transfer of the disputed funds and collateral to the arbitrator's control.

Fund Transfer Mechanism:

For Multisig Escrow: The arbitrator is part of a 3-of-3 multisig wallet, and with both party's cooperation, can access the funds.

For Lightning Network Payments: The clients initiate a payment to the arbitrator's LN node equivalent to the disputed amount plus any fees.

Step 6: Off-Protocol Arbitration Proceedings

The arbitrator communicates with both parties outside the protocol to:

Gather Information: Collect evidence, statements, and any necessary documents.

Deliberate: Analyze the information to make a fair decision.

Confidentiality: Ensure privacy and confidentiality of sensitive data.

Step 7: Arbitrator Disburses Funds Off-Protocol

Based on the arbitration outcome:

Fund Distribution: The arbitrator disburses the funds and collateral to the appropriate parties using off-protocol transactions.

Payment to Seller or Refund to Buyer: The arbitrator sends the funds directly to the entitled party's Bitcoin or LN address.

Deduction of Arbitration Fee: The arbitrator deducts their fee from the funds before disbursal, as per the agreed terms.

Arbitration events happen off protocol because of the inherent complexity of disputes.  It would be impractical to try to account for every possible dispute solution.

Step 8: Closing the Dispute on Protocol

While the actual fund transfer happens off-protocol, the arbitrator publishes a kind-317 event to record the resolution.

Arbitrator's Resolution Event (kind-317):

{

&nbsp; "kind": 317,

&nbsp; "content": {

&nbsp;   "dispute\_ref": "event\_id\_312",

&nbsp;   "resolution": "Funds refunded to buyer as item was not delivered.",

&nbsp;   "arbitration\_fee\_satoshis": 1600000,

&nbsp;   "fee\_deducted\_from": "seller\_collateral"

&nbsp; },

&nbsp; "pubkey": "arbitrator\_pubkey",

&nbsp; "sig": "signature\_arbitrator\_317",

&nbsp; "relays": \["relay1.example.com"],

&nbsp; "id": "event\_id\_317",

&nbsp; "created\_at": 1620001100

}



Purpose: This event provides a public record of the dispute's resolution.

Step 9: Rating the Arbitrator (kind-322)

Both parties can provide feedback on the arbitrator's performance.



Scenarios Demonstrating Potential Exchanges

Scenario 1: Successful Transaction

Process Summary:

Seller Lists Product (kind-300).

Seller Deposits Collateral (kind-310).

Buyer Submits Bid (kind-301).

Seller Accepts Bid (kind-303).

Buyer Deposits Collateral \& Confirms Payment (kind-311).

Escrow Activated.

Seller Ships Item and Notifies Buyer (kind-320).

Buyer Confirms Receipt (kind-313).

Funds and Collateral Released.

Feedback Submitted (kind-321).

Scenario 2: Buyer Does Not Confirm Receipt

Seller Lists Product (kind-300).

Seller Deposits Collateral (kind-310).

Buyer Submits Bid (kind-301).

Seller Accepts Bid (kind-303).

Buyer Deposits Collateral \& Confirms Payment (kind-311).

Escrow Activated.

Seller Ships Item and Notifies Buyer (kind-320).

Buyer Fails to Confirm Receipt.  All funds including the buyers collateral remain locked in escrow.

Seller messages the buyer requesting confirmation of receipt (kind-320)

Buyer confirms receipt to recover their collateral (kind-313)

Buyer disputes the receipt of item

Seller or buyer Initiates a Dispute (kind-312)

Arbitration is offered (kind-316)

Mutual Agreement is made (kind 315) by both parties to have 3rd party resolve the issue off protocol

Mutual Agreement fails and all parties’ fund remain locked

Scenario 3: Seller Fails to Ship the Item

Additional Steps:

Buyer Initiates Communication (kind-320).

Mutual Agreement to Cancel (kind-315).

Funds and Collateral Returned.



Potential Attack Vectors and Mitigation Strategies

1\. Client Software Manipulation

Threat: Users may modify client software to bypass protocol rules, potentially releasing escrowed funds without proper authorization.

Mitigation Strategies:

Cryptographic Enforcement:

All events must be signed using the user's private key.

Events include references to previous events, creating an immutable chain.

Clients and relays verify signatures and event integrity before processing.

Protocol Compliance Checks:

Clients enforce protocol rules by validating event structures and sequences.

Non-compliant events are rejected, preventing unauthorized actions.

Community Standards:

Promote the use of open-source, audited client software.

Encourage users to verify the authenticity of their client software.

2\. Sybil Attacks

Threat: An attacker creates multiple fake identities to manipulate reputation scores or flood the network with spam.

Mitigation Strategies:

Require Proof of Work (PoW) or small LN payments for certain actions, increasing the cost of creating unlimited events to manipulate the system.

Relays set their own anti-spam policies, filtering out spam.

Possibility to assign more weight to feedback from users with established reputations.

Limiting ratings to actual sale events

3\. Denial of Service (DoS) Attacks

Threat: Attackers flood relays with bogus events, causing service degradation.

Mitigation Strategies:

Relays or clients may implement rate limits to control the flow of events.

Relays or clients may Increase PoW difficulty during high traffic periods.

Clients and users can switch to alternative relays if one becomes unresponsive.

4\. Man-in-the-Middle (MitM) Attacks

Threat: Attackers intercept and alter communication between parties.

Mitigation Strategies:

End-to-End Encryption:

Sensitive messages can be encrypted using the recipient's public key.

Only the intended recipient can decrypt and read the message.

Digital Signatures:

All events are digitally signed by the sender.

Recipients verify signatures to ensure authenticity and integrity.

Secure Communication Channels:

Use secure transport protocols (e.g., TLS) where applicable.

5\. Replay Attacks

Threat: Attackers resend valid events to manipulate the protocol's state.

Mitigation Strategies:

Event Identifiers and Timestamps:

Each event includes a unique ID and timestamp.

Clients track processed events to prevent duplicate processing.

Nonces and Sequence Numbers:

Incorporate nonces or sequence numbers in events.

Events with unexpected sequence numbers are rejected.

6\. Collusion Between Parties

Threat: Parties collude to defraud others, such as a buyer and arbitrator working together against a seller.

Mitigation Strategies:

Negative feedback from affected parties impacts the reputation of colluding users.

Future participants can avoid interacting with low-reputation users.

All events, including arbitration agreements and outcomes, are publicly recorded.

Suspicious patterns can be detected by the community.

Funds cannot be released without mutual agreement, reducing the impact of collusion.

Make it so arbitrators can be chosen at random based on reputation scores.

7\. Privacy Attacks

Threat: Observers analyze public events to link transactions and identify users.

Mitigation Strategies:

Encrypt messages containing sensitive information.

Avoid including personal data in public event fields.

Only essential information is included in events.

Sensitive details can be shared off-protocol or within encrypted messages.





Conclusion

DOMP’s decentralized approach addresses key challenges in security, fraud prevention, and trust-building within online marketplaces. By fostering collaboration among developers and users, DOMP has the potential to contribute significantly to the future of peer-to-peer commerce.

Enhanced Buyer Confidence: Requiring the seller to post collateral first reduces the risk of trolling and demonstrates commitment.

Explicit Escrow Establishment: The escrow mechanism is clearly defined, using LN invoices and protocol agreements without requiring third-party escrow agents.

Combined Payment and Collateral Confirmation: By integrating the buyer's collateral deposit and payment confirmation into a single event (kind-311), the protocol ensures that buyers cannot bypass collateral requirements, enhancing security.

Effective Communication: Incorporating kind-320 events allows for seamless communication between parties, such as shipping notifications.

Robust Reputation System with Abuse Prevention: Requiring kind-321 events to reference specific previous events ensures that only parties involved in a transaction can rate each other, preventing abuse of the rating system.

Exclusive Buyer Control Over Funds Release: Buyers alone can release funds from escrow unless mutual agreement or arbitration is initiated.

No Unilateral Seller Access to Escrowed Funds: Sellers must fulfill their obligations to access payments.

Optional Arbitration and Third Parties: The protocol allows for third-party involvement only when both parties agree.

Market-Driven Anti-Spam Measures: Relays set their own anti-spam policies, promoting a dynamic and adaptable network.

Event Integrity and Security: Strict event structures and cryptographic references ensure transaction integrity without centralized oversight.

Trade-offs and Reasonings:

Combined Payment and Collateral Confirmation: Enhances security by ensuring that the buyer cannot confirm payment without simultaneously depositing their collateral.

Mandatory Event References in Reputation Feedback: Prevents abuse by ensuring that only participants in a transaction can submit feedback, and each transaction can only be rated once.

Separate Event Types for Bid Acceptance and Counter Bids: Enhances clarity and reduces the risk of misunderstandings.

Seller Posts Collateral First: Increases buyer confidence without adding risk to the seller, as they can refund funds if the buyer disengages.

Optional Third-Party Involvement: Maintains decentralization and user autonomy, allowing flexibility when disputes arise.

Reputation System Universality: By storing reputation events on Nostr relays, reputation scores are universally accessible and consistent across clients, while calculations are performed by clients following standardized methods.

Realizing the vision of DOMP’s decentralized approach requires collaborative efforts from the community. Interested parties are encouraged to contribute to the development and implementation of this protocol. If you are interested in being involved contact me on nostr @Fromperdomp

npub19n4ecg8l4l3fxe0muam78zth0hudt3l64fgezz20hyahcwq42sss587dtv











